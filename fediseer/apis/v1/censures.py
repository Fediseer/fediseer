from fediseer.apis.v1.base import *
from fediseer.classes.instance import Censure
from fediseer.utils import sanitize_string
from fediseer.classes.reports import Report
from fediseer import enums
from fediseer.register import ensure_instance_registered

class CensuresGiven(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=False, help="An instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")
    get_parser.add_argument("min_censures", required=False, default=1, type=int, help="Limit to this amount of censures of more", location="args")
    get_parser.add_argument("reasons_csv", required=False, type=str, help="Only retrieve censures where their reasons include any of the text in this csv", location="args")
    get_parser.add_argument("page", required=False, type=int, default=1, help="Which page of results to retrieve. Only unfiltered results will be paginated.", location="args")
    get_parser.add_argument("limit", required=False, type=int, default=1000, help="Which amount of results to retrieve. Only unfiltered results will be limited.", location="args")

    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Censures_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    @api.response(401, 'API key not found', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    def get(self, domains_csv):
        '''Display all censures given out by one or more domains
        You can pass a comma-separated list of domain names
        and the results will be a set of all their censures together.
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
            if p_instance.visibility_censures == enums.ListVisibility.ENDORSED:
                if get_instance is None:
                    continue
                if p_instance != get_instance and not p_instance.is_endorsing(get_instance):
                    continue
            if p_instance.visibility_censures == enums.ListVisibility.PRIVATE:
                if get_instance is None:
                    continue
                if p_instance != get_instance:
                    continue
            instances.append(p_instance)
        if len(instances) == 0:
            raise e.Forbidden(f"You do not have access to see these censures")
        if self.args.min_censures > len(instances):
            raise e.BadRequest(f"You cannot request more censures than the amount of reference domains")
        instance_details = []
        limit = self.args.limit
        if self.args.reasons_csv:
            limit = None
        if self.args.min_censures and self.args.min_censures != 1:
            limit = None
        for c_instance in database.get_all_censured_instances_by_censuring_id(
            censuring_ids = [instance.id for instance in instances],
            page=self.args.page,
            limit=limit,
        ):
            censures = database.get_all_censure_reasons_for_censured_id(c_instance.id, [instance.id for instance in instances])
            censure_count = len(censures)
            censures = [c for c in censures if c.reason is not None]
            c_instance_details = c_instance.get_details()
            skip_instance = True
            if self.args.reasons_csv:
                reasons_filter = [r.strip().lower() for r in self.args.reasons_csv.split(',')]
                reasons_filter = set(reasons_filter)
                if "__all_pedos__" in reasons_filter:
                    reasons_filter.add("csam")
                    reasons_filter.add("loli")
                    reasons_filter.add("shota")
                    reasons_filter.add("pedophil")
                if "__all_bigots__" in reasons_filter:
                    reasons_filter.add("racism")
                    reasons_filter.add("sexism")
                    reasons_filter.add("transphobia")
                    reasons_filter.add("homophobia")
                    reasons_filter.add("islamophobia")
                    reasons_filter.add("nazi")
                    reasons_filter.add("fascist")
                    reasons_filter.add("hate speech")
                    reasons_filter.add("bigotry")
                for r in reasons_filter:
                    reason_filter_counter = 0
                    for censure in censures:
                        if r in censure.reason.lower():
                            reason_filter_counter += 1
                    if reason_filter_counter >= self.args.min_censures:
                        skip_instance = False
                        break
            elif censure_count >= self.args.min_censures:
                skip_instance = False
            if skip_instance:
                continue
            c_instance_details["censure_reasons"] = [censure.reason for censure in censures]
            c_instance_details["censure_evidence"] = [censure.evidence for censure in censures if censure.evidence is not None]
            c_instance_details["censure_count"] = censure_count
            instance_details.append(c_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        
        return {"instances": instance_details},200

class Censures(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=False, help="An instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Censures_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all censures received by a specific domain
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
        precheck_instances = database.get_all_censuring_instances_by_censured_id(instance.id)
        instances = []
        for p_instance in precheck_instances:
            if p_instance.visibility_censures == enums.ListVisibility.ENDORSED:
                if get_instance is None:
                    continue
                if not p_instance.is_endorsing(get_instance):
                    continue
            if p_instance.visibility_censures == enums.ListVisibility.PRIVATE:
                if get_instance is None:
                    continue
                if p_instance != get_instance:
                    continue
            instances.append(p_instance)
        censures = database.get_all_censure_reasons_for_censured_id(instance.id, [c.id for c in instances])
        rebuttals = database.get_all_rebuttals_from_source_instance_id(instance.id,[c.id for c in instances])
        for c_instance in instances:
            censures = [c for c in censures if c.reason is not None and c.censuring_id == c_instance.id]
            c_instance_details = c_instance.get_details()
            if len(censures) > 0:
                c_instance_details["censure_reasons"] = [censure.reason for censure in censures]
                c_instance_details["censure_evidence"] = [censure.evidence for censure in censures if censure.evidence is not None]
                rebuttals = [r.rebuttal for r in rebuttals if r.target_id == c_instance.id]
                if len(rebuttals) > 0 and not database.instance_has_flag(c_instance.id,enums.InstanceFlags.MUTED):
                    c_instance_details["rebuttal"] = rebuttals
            instance_details.append(c_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("reason", default=None, type=str, required=False, location="json")
    put_parser.add_argument("evidence", default=None, type=str, required=False, location="json")


    @api.expect(put_parser,models.input_censures_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Censure Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Censure an instance
        A censure signifies a strong disapproval from your instance to how that instance is being run.
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can censure others.")
        if database.instance_has_flag(instance.id,enums.InstanceFlags.RESTRICTED):
            raise e.Forbidden("You cannot take this action as your instance is restricted")
        if instance.domain == domain:
            raise e.BadRequest("You're a mad lad, but you can't censure yourself.")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance, instance_info = ensure_instance_registered(domain, allow_unreachable=True)
        if not target_instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        if database.get_endorsement(target_instance.id,instance.id):
            raise e.BadRequest("You can't censure an instance you've endorsed! Please withdraw the endorsement first.")
        if database.get_censure(target_instance.id,instance.id):
            return {"message":'OK'}, 200
        if database.count_all_censured_instances_by_censuring_id([instance.id]) >= instance.max_list_size:
            raise e.Forbidden("You're reached the maximum amount of instances you can add to your censures. Please contact the admins of fediseer to increase this limit is needed.")
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
        evidence = self.args.evidence
        if evidence is not None:
            evidence = sanitize_string(evidence)
        new_censure = Censure(
            censuring_id=instance.id,
            censured_id=target_instance.id,
            reason=reason,
            evidence=evidence,
        )
        db.session.add(new_censure)
        target_domain = target_instance.domain
        if instance.visibility_censures != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.CENSURE,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Censured {domain}")
        return {"message":'Changed'}, 200


    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("reason", default=None, type=str, required=False, location="json")
    patch_parser.add_argument("evidence", default=None, type=str, required=False, location="json")


    @api.expect(patch_parser,models.input_censures_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Modify Instance Censure')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def patch(self, domain):
        '''Modify an instance's Censure
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
            raise e.BadRequest("Instance from which to modify censure not found")
        censure = database.get_censure(target_instance.id,instance.id)
        if not censure:
            raise e.BadRequest(f"No censure found for {domain} from {instance.domain}")
        changed = False
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
            if censure.reason != reason:
                censure.reason = reason
                changed = True
        evidence = self.args.evidence
        if evidence is not None:
            evidence = sanitize_string(evidence)
            if censure.evidence != evidence:
                censure.evidence = evidence
                changed = True
        if changed is False:
            return {"message":'OK'}, 200
        target_domain = target_instance.domain
        if instance.visibility_censures != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.CENSURE,
            report_activity=enums.ReportActivity.MODIFIED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} modIfied censure for {domain}")
        return {"message":'Changed'}, 200


    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Withdraw Instance Censure')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def delete(self,domain):
        '''Withdraw an instance censure
        '''
        self.args = self.delete_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to withdraw censure not found")
        censure = database.get_censure(target_instance.id,instance.id)
        if not censure:
            return {"message":'OK'}, 200
        db.session.delete(censure)
        target_domain = target_instance.domain
        if instance.visibility_censures != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.CENSURE,
            report_activity=enums.ReportActivity.DELETED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Withdrew censure from {domain}")
        return {"message":'Changed'}, 200


class BatchCensures(Resource):

    decorators = [limiter.limit("2/minute", key_func = get_request_path)]
    post_parser = reqparse.RequestParser()
    post_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    post_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    post_parser.add_argument("delete", required=False, default=False, type=bool, help="Set to true, to delete all censures which are not in the censures list", location="json")
    post_parser.add_argument("overwrite", required=False, default=False, type=bool, help="Set to true, to modify all existing entries with new data", location="json")
    post_parser.add_argument("censures", default=None, type=list, required=True, location="json")


    @api.expect(post_parser,models.input_batch_censures, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Batch Censure Instances')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def post(self):
        '''Batch Censure instances
        '''
        self.args = self.post_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can censure others.")
        if database.instance_has_flag(instance.id,enums.InstanceFlags.RESTRICTED):
            raise e.Forbidden("You cannot take this action as your instance is restricted")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        if self.args.delete is True:
            if len(self.args.censures) >= instance.max_list_size:
                raise e.Forbidden("You're specified more than maximum amount of instances you can add to your censures. Please contact the admins of fediseer to increase this limit is needed.")
        else:
            if database.count_all_censured_instances_by_censuring_id([instance.id]) + len(self.args.censures) >= instance.max_list_size:
                raise e.Forbidden("You're reached the maximum amount of instances you can add to your censures. Please contact the admins of fediseer to increase this limit is needed.")
            if len(self.args.censures) == 0:
                raise e.BadRequest("You have not provided any entries to append to your censures.")
        added_entries = 0
        deleted_entries = 0
        modified_entries = 0
        seen_domains = set()
        if self.args.delete:
            existing_censures = database.get_all_censured_instances_by_censuring_id([instance.id], limit=None)
            new_censures = set([c["domain"] for c in self.args.censures])
            for target_instance in existing_censures:
                if target_instance.domain not in new_censures:
                    old_censure = database.get_censure(target_instance.id,instance.id)
                    db.session.delete(old_censure)
                    deleted_entries += 1
        for entry in self.args.censures:
            if entry["domain"] in seen_domains:
                logger.info(f"Batch censure operation by {instance.domain} had duplicate entries for {entry['domain']}")
                continue
            seen_domains.add(entry["domain"])
            if instance.domain == entry["domain"]:
                continue
            target_instance, instance_info = ensure_instance_registered(entry["domain"], allow_unreachable=True)
            reason = entry.get("reason")
            if reason is not None:
                reason = sanitize_string(reason)
            evidence = entry.get("evidence")
            if evidence is not None:
                evidence = sanitize_string(evidence)
            if not target_instance:
                continue
            if database.get_endorsement(target_instance.id,instance.id):
                continue
            censure = database.get_censure(target_instance.id,instance.id)            
            if censure:
                if self.args.overwrite is False:
                    continue
                if censure.reason == reason and censure.evidence == evidence:  
                    continue
                censure.reason = reason
                censure.evidence = evidence
                modified_entries += 1
            else:             
                new_censure = Censure(
                    censuring_id=instance.id,
                    censured_id=target_instance.id,
                    reason=reason,
                    evidence=evidence,
                )
                db.session.add(new_censure)
                added_entries += 1
        if added_entries + deleted_entries + modified_entries == 0:
            return {"message":'OK'}, 200
        if added_entries > 0:
            new_report = Report(
                source_domain=instance.domain,
                target_domain='[MULTIPLE]',
                report_type=enums.ReportType.CENSURE,
                report_activity=enums.ReportActivity.ADDED,
            )
            db.session.add(new_report)
        if modified_entries > 0:
            new_report = Report(
                source_domain=instance.domain,
                target_domain='[MULTIPLE]',
                report_type=enums.ReportType.CENSURE,
                report_activity=enums.ReportActivity.MODIFIED,
            )
            db.session.add(new_report)
        if deleted_entries > 0:
            new_report = Report(
                source_domain=instance.domain,
                target_domain='[MULTIPLE]',
                report_type=enums.ReportType.CENSURE,
                report_activity=enums.ReportActivity.DELETED,
            )
            db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Batched Censures for {added_entries + modified_entries + deleted_entries} domains.")
        return {"message":'Changed'}, 200