from fediseer.apis.v1.base import *
from fediseer.classes.instance import Endorsement,Censure
from fediseer.classes.reports import Report
from fediseer import enums
from fediseer.utils import sanitize_string
from fediseer.register import ensure_instance_registered

class Approvals(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=False, help="An instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")
    get_parser.add_argument("min_endorsements", required=False, default=1, type=int, help="Limit to this amount of endorsements of more", location="args")
    get_parser.add_argument("reasons_csv", required=False, type=str, help="Only retrieve endorsements where their reasons include any of the text in this csv", location="args")
    get_parser.add_argument("page", required=False, type=int, default=1, help="Which page of results to retrieve.", location="args")
    get_parser.add_argument("limit", required=False, type=int, default=1000, help="Which amount of results to retrieve.", location="args")

    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Endorsed_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    @api.response(401, 'API key not found', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    def get(self, domains_csv):
        '''Display all endorsements given out by one or more domains
        You can pass a comma-separated list of domain names and the results will be a set of all their
        endorsements together.
        '''
        self.args = self.get_parser.parse_args()
        # if self.args.limit > 100: # Once limit is in effect
        #     raise e.BadRequest("limit cannot be more than 100")
        if self.args.limit < 10:
            raise e.BadRequest("Limit cannot be less than 10")
        get_instance = None
        if self.args.apikey:
            get_instance = database.find_instance_by_api_key(self.args.apikey)
            if not get_instance:
                raise e.Unauthorized(f"No Instance found matching provided API key. Please ensure you've typed it correctly")
        domains_list = domains_csv.split(',')
        precheck_instances = database.find_multiple_instance_by_domains(domains_list)
        if not precheck_instances:
            raise e.NotFound(f"No Instances found matching any of the provided domains. Have you remembered to register them?")
        instances = []
        for p_instance in precheck_instances:
            if p_instance.visibility_endorsements == enums.ListVisibility.ENDORSED:
                if get_instance is None:
                    continue
                if p_instance != get_instance and not p_instance.is_endorsing(get_instance):
                    continue
            if p_instance.visibility_endorsements == enums.ListVisibility.PRIVATE:
                if get_instance is None:
                    continue
                if p_instance != get_instance:
                    continue
            instances.append(p_instance)
        if len(instances) == 0:
            raise e.Forbidden(f"You do not have access to see these endorsements")
        if self.args.min_endorsements > len(instances):
            raise e.BadRequest(f"You cannot request more endorsements than the amount of reference domains")
        instance_details = []
        endorsements = database.get_all_endorsements_from_approving_id([instance.id for instance in instances])
        for e_instance in database.get_all_endorsed_instances_by_approving_id(
            approving_ids=[instance.id for instance in instances],
            page=self.args.page,
            limit=self.args.limit,
        ):
            e_endorsements = [e for e in endorsements if e.endorsed_id == e_instance.id]
            endorsement_count = len(e_endorsements)
            r_endorsements = [e for e in e_endorsements if e.reason is not None]
            if self.args.csv or self.args.domains:
                e_instance_details = {"domain": e_instance.domain}
            else:
                e_instance_details = e_instance.get_details()
            skip_instance = True
            if self.args.reasons_csv:
                reasons_filter = [r.strip().lower() for r in self.args.reasons_csv.split(',')]
                reasons_filter = set(reasons_filter)
                for r in reasons_filter:
                    reason_filter_counter = 0
                    for endorsement in r_endorsements:
                        if r in endorsement.reason.lower():
                            reason_filter_counter += 1
                    if reason_filter_counter >= self.args.min_endorsements:
                        skip_instance = False
                        break
            elif endorsement_count >= self.args.min_endorsements:
                skip_instance = False
            if skip_instance:
                continue
            e_instance_details["endorsement_reasons"] = [endorsement.reason for endorsement in r_endorsements]
            instance_details.append(e_instance_details)
        if self.args.csv:
            return {
                "csv": ",".join([instance["domain"] for instance in instance_details]),
                "total": len(endorsements)
            },200
        if self.args.domains:
            return {
                "domains": [instance["domain"] for instance in instance_details],
                "total": len(endorsements)
            },200
        return {
            "instances": instance_details,
            "total": len(endorsements)
        },200

class Endorsements(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=False, help="An instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Endorsed_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all endorsements received by a specific domain
        '''
        self.args = self.get_parser.parse_args()
        get_instance = None
        if self.args.apikey:
            get_instance = database.find_instance_by_api_key(self.args.apikey)
            if not get_instance:
                raise e.Unauthorized(f"No Instance found matching provided API key. Please ensure you've typed it correctly")
        instance = database.find_instance_by_domain(domain)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided domain. Have you remembered to register it?")
        instance_details = []
        precheck_instances = database.get_all_approving_instances_by_endorsed_id(instance.id)
        instances = []
        for p_instance in precheck_instances:
            if p_instance.visibility_endorsements == enums.ListVisibility.ENDORSED:
                if get_instance is None:
                    continue
                if not p_instance.is_endorsing(get_instance):
                    continue
            if p_instance.visibility_endorsements == enums.ListVisibility.PRIVATE:
                if get_instance is None:
                    continue
                if p_instance != get_instance:
                    continue
            instances.append(p_instance)
        for e_instance in instances:
            endorsements = database.get_all_endorsement_reasons_for_endorsed_id(instance.id, [e_instance.id])
            endorsements = [e for e in endorsements if e.reason is not None]
            e_instance_details = e_instance.get_details()
            if len(endorsements) > 0:
                e_instance_details["endorsement_reasons"] = [endorsement.reason for endorsement in endorsements]
            instance_details.append(e_instance_details)
        if self.args.csv:
            return {
                "csv": ",".join([instance["domain"] for instance in instance_details]),
                "total": len(instances)
            },200
        if self.args.domains:
            return {
                "domains": [instance["domain"] for instance in instance_details],
                "total": len(instances)
            },200
        return {
            "instances": instance_details,
            "total": len(instances)
        },200


    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("reason", default=None, type=str, required=False, location="json")
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")


    @api.expect(put_parser,models.input_endorsements_modify)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Endorse Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Endorse an instance
        An endorsement signifies an approval from your instance to how that instance is being run.
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can endorse others.")
        if database.instance_has_flag(instance.id,enums.InstanceFlags.RESTRICTED):
            raise e.Forbidden("You cannot take this action as your instance is restricted")
        if instance.domain == domain:
            raise e.BadRequest("Nice try, but you can't endorse yourself.")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance, instance_info = ensure_instance_registered(domain)
        if not target_instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        if len(target_instance.guarantors) == 0:
            raise e.Forbidden("Not Guaranteed instances can be endorsed. Please guarantee for them, or find someone who will.")
        if not target_instance:
            raise e.BadRequest("Instance to endorse not found")
        if database.get_censure(target_instance.id,instance.id):
            raise e.BadRequest("You can't endorse an instance you've censured! Please withdraw the censure first.")
        if database.get_endorsement(target_instance.id,instance.id):
            return {"message":'OK'}, 200
        if database.count_all_endorsed_instances_by_approving_id([instance.id]) >= instance.max_list_size:
            raise e.Forbidden("You're reached the maximum amount of instances you can add to your endorsements. Please contact the admins of fediseer to increase this limit is needed.")
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
        new_endorsement = Endorsement(
            approving_id=instance.id,
            endorsed_id=target_instance.id,
            reason=reason,
        )
        db.session.add(new_endorsement)
        target_domain = target_instance.domain
        if instance.visibility_endorsements != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.ENDORSEMENT,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        # if not database.has_recent_endorsement(target_instance.id):
        try:
            if instance.visibility_endorsements != enums.ListVisibility.PRIVATE:
                message = f"Your instance has just been [endorsed](https://fediseer.com/faq#what-is-an-endorsement) by {instance.domain}."
                if reason is not None:
                    message = f"Your instance has just been [endorsed](https://fediseer.com/faq#what-is-an-endorsement) by {instance.domain} with reason: {reason}"
                activitypub_pm.pm_admins(
                    message=message,
                    domain=target_instance.domain,
                    software=target_instance.software,
                    instance=target_instance,
                )
        except:
            pass
        logger.info(f"{instance.domain} Endorsed {domain}")
        return {"message":'Changed'}, 200

    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("reason", default=None, type=str, required=False, location="json")


    @api.expect(patch_parser,models.input_endorsements_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Modify Endorsement')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def patch(self, domain):
        '''Modify an existing endorsement
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance for which to modify endorsement not found")
        endorsement = database.get_endorsement(target_instance.id,instance.id)
        if not endorsement:
            raise e.BadRequest(f"No endorsement found for {domain} from {instance.domain}")
        changed = False
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
            if endorsement.reason != reason:
                endorsement.reason = reason
                changed = True
        if changed is False:
            return {"message":'OK'}, 200
        target_domain = target_instance.domain
        if instance.visibility_endorsements != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.ENDORSEMENT,
            report_activity=enums.ReportActivity.MODIFIED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Modified endorsement for {domain}")
        return {"message":'Changed'}, 200


    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Withdraw Instance Endorsement')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def delete(self,domain):
        '''Withdraw an instance endorsement
        '''
        self.args = self.delete_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to withdraw endorsement not found")
        endorsement = database.get_endorsement(target_instance.id,instance.id)
        if not endorsement:
            return {"message":'OK'}, 200
        db.session.delete(endorsement)
        target_domain = target_instance.domain
        if instance.visibility_endorsements != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.ENDORSEMENT,
            report_activity=enums.ReportActivity.DELETED,
        )
        db.session.add(new_report)
        db.session.commit()
        try:
            if instance.visibility_endorsements != enums.ListVisibility.PRIVATE:
                activitypub_pm.pm_admins(
                    message=f"Oh no. {instance.domain} has just withdrawn the endorsement of your instance",
                    domain=target_instance.domain,
                    software=target_instance.software,
                    instance=target_instance,
                )
        except:
            pass
        logger.info(f"{instance.domain} Withdrew endorsement from {domain}")
        return {"message":'Changed'}, 200


class BatchEndorsements(Resource):

    decorators = [limiter.limit("2/minute", key_func = get_request_path)]
    post_parser = reqparse.RequestParser()
    post_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    post_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    post_parser.add_argument("delete", required=False, default=False, type=bool, location="json")
    post_parser.add_argument("overwrite", required=False, default=False, type=bool, location="json")
    post_parser.add_argument("endorsements", default=None, type=list, required=True, location="json")


    @api.expect(post_parser,models.input_batch_endorsements, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Batch Endorse Instances')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def post(self):
        '''Batch Endorse instances
        '''
        self.args = self.post_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can endorse others.")
        if database.instance_has_flag(instance.id,enums.InstanceFlags.RESTRICTED):
            raise e.Forbidden("You cannot take this action as your instance is restricted")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        if self.args.delete is True:
            if len(self.args.endorsements) >= instance.max_list_size:
                raise e.Forbidden("You're specified more than maximum amount of instances you can add to your endorsements. Please contact the admins of fediseer to increase this limit is needed.")
        else:
            if database.count_all_endorsed_instances_by_approving_id([instance.id]) + len(self.args.endorsements) >= instance.max_list_size:
                raise e.Forbidden("You're reached the maximum amount of instances you can add to your endorsements. Please contact the admins of fediseer to increase this limit is needed.")
            if len(self.args.endorsements) == 0:
                raise e.BadRequest("You have not provided any entries to append to your endorsements.")
        added_entries = 0
        deleted_entries = 0
        modified_entries = 0
        seen_domains = set()
        if self.args.delete:
            existing_endorsements = database.get_all_endorsed_instances_by_approving_id([instance.id], limit=None)
            new_endorsements = set([c["domain"] for c in self.args.endorsements])
            for target_instance in existing_endorsements:
                if target_instance.domain not in new_endorsements:
                    old_endorsement = database.get_endorsement(target_instance.id,instance.id)
                    db.session.delete(old_endorsement)
                    deleted_entries += 1
        for entry in self.args.endorsements:
            if entry["domain"] in seen_domains:
                logger.info(f"Batch endorsement operation by {instance.domain} had duplicate entries for {entry['domain']}")
                continue
            seen_domains.add(entry["domain"])
            if instance.domain == entry["domain"]:
                continue
            target_instance, instance_info = ensure_instance_registered(entry["domain"], allow_unreachable=True)
            reason = entry.get("reason")
            if reason is not None:
                reason = sanitize_string(reason)
            if not target_instance:
                continue
            if database.get_censure(target_instance.id,instance.id):
                continue
            if database.get_hesitation(target_instance.id,instance.id):
                continue
            endorsement = database.get_endorsement(target_instance.id,instance.id)            
            if endorsement:
                if self.args.overwrite is False:
                    continue
                if endorsement.reason == reason:  
                    continue
                endorsement.reason = reason
                modified_entries += 1
            else:             
                new_endorsement = Endorsement(
                    approving_id=instance.id,
                    endorsed_id=target_instance.id,
                    reason=reason,
                )
                db.session.add(new_endorsement)
                added_entries += 1
        if added_entries + deleted_entries + modified_entries == 0:
            return {"message":'OK'}, 200
        if added_entries > 0:
            new_report = Report(
                source_domain=instance.domain,
                target_domain='[MULTIPLE]',
                report_type=enums.ReportType.ENDORSEMENT,
                report_activity=enums.ReportActivity.ADDED,
            )
            db.session.add(new_report)
        if modified_entries > 0:
            new_report = Report(
                source_domain=instance.domain,
                target_domain='[MULTIPLE]',
                report_type=enums.ReportType.ENDORSEMENT,
                report_activity=enums.ReportActivity.MODIFIED,
            )
            db.session.add(new_report)
        if deleted_entries > 0:
            new_report = Report(
                source_domain=instance.domain,
                target_domain='[MULTIPLE]',
                report_type=enums.ReportType.ENDORSEMENT,
                report_activity=enums.ReportActivity.DELETED,
            )
            db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Batched endorsements for {added_entries + modified_entries + deleted_entries} domains.")
        return {"message":'Changed'}, 200