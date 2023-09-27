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
    get_parser.add_argument("page", required=False, type=int, default=1, help="Which page of results to retrieve", location="args")
    get_parser.add_argument("limit", required=False, type=int, default=10, help="Which page of results to retrieve", location="args")

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
        domains_list = domains_csv.split(',')
        self.args = self.get_parser.parse_args()
        get_instance = None
        if self.args.apikey:
            get_instance = database.find_instance_by_api_key(self.args.apikey)
            if not get_instance:
                raise e.Unauthorized(f"No Instance found matching provided API key. Please ensure you've typed it correctly")
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
        instance_details = []
        for e_instance in database.get_all_endorsed_instances_by_approving_id([instance.id for instance in instances]):
            endorsements = database.get_all_endorsement_reasons_for_endorsed_id(e_instance.id, [instance.id for instance in instances])
            endorsement_count = len(endorsements)
            endorsements = [e for e in endorsements if e.reason is not None]
            e_instance_details = e_instance.get_details()
            skip_instance = True
            if self.args.reasons_csv:
                reasons_filter = [r.strip().lower() for r in self.args.reasons_csv.split(',')]
                reasons_filter = set(reasons_filter)
                for r in reasons_filter:
                    reason_filter_counter = 0
                    for endorsement in endorsements:
                        if r in endorsement.reason.lower():
                            reason_filter_counter += 1
                    if reason_filter_counter >= self.args.min_endorsements:
                        skip_instance = False
                        break
            elif endorsement_count >= self.args.min_endorsements:
                skip_instance = False
            if skip_instance:
                continue
            e_instance_details["endorsement_reasons"] = [endorsement.reason for endorsement in endorsements]
            instance_details.append(e_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

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
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

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
