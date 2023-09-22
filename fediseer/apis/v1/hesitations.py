from fediseer.apis.v1.base import *
from fediseer.classes.instance import Hesitation
from fediseer.utils import sanitize_string
from fediseer.classes.reports import Report
from fediseer import enums

class HesitationsGiven(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=False, help="An instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")
    get_parser.add_argument("min_hesitations", required=False, default=1, type=int, help="Limit to this amount of hesitations of more", location="args")
    get_parser.add_argument("reasons_csv", required=False, type=str, help="Only retrieve hesitations where their reasons include any of the text in this csv", location="args")

    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Hesitations_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    @api.response(401, 'API key not found', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    def get(self, domains_csv):
        '''Display all hesitations given out by one or more domains
        You can pass a comma-separated list of domain names
        and the results will be a set of all their hesitations together.
        '''
        self.args = self.get_parser.parse_args()
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
            if p_instance.visibility_hesitations == enums.ListVisibility.ENDORSED:
                if get_instance is None:
                    continue
                if p_instance != get_instance and not p_instance.is_endorsing(get_instance):
                    continue
            if p_instance.visibility_hesitations == enums.ListVisibility.PRIVATE:
                if get_instance is None:
                    continue
                if p_instance != get_instance:
                    continue
            instances.append(p_instance)
        if len(instances) == 0:
            raise e.Forbidden(f"You do not have access to see these hesitations")
        if self.args.min_hesitations > len(instances):
            raise e.BadRequest(f"You cannot request more hesitations than the amount of reference domains")
        instance_details = []
        for c_instance in database.get_all_dubious_instances_by_hesitant_id([instance.id for instance in instances]):
            hesitations = database.get_all_hesitation_reasons_for_dubious_id(c_instance.id, [instance.id for instance in instances])
            hesitation_count = len(hesitations)
            hesitations = [c for c in hesitations if c.reason is not None]
            c_instance_details = c_instance.get_details()
            skip_instance = True
            if self.args.reasons_csv:
                reasons_filter = [r.strip().lower() for r in self.args.reasons_csv.split(',')]
                reasons_filter = set(reasons_filter)
                for r in reasons_filter:
                    reason_filter_counter = 0
                    for hesitation in hesitations:
                        if r in hesitation.reason.lower():
                            reason_filter_counter += 1
                    if reason_filter_counter >= self.args.min_hesitations:
                        skip_instance = False
                        break
            elif hesitation_count >= self.args.min_hesitations:
                skip_instance = False
            if skip_instance:
                continue
            c_instance_details["hesitation_reasons"] = [hesitation.reason for hesitation in hesitations]
            c_instance_details["hesitation_evidence"] = [hesitation.evidence for hesitation in hesitations if hesitation.evidence is not None]
            c_instance_details["hesitation_count"] = hesitation_count
            instance_details.append(c_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        
        return {"instances": instance_details},200

class Hesitations(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=False, help="An instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Hesitations_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all hesitations received by a specific domain
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
        precheck_instances = database.get_all_hesitant_instances_by_dubious_id(instance.id)
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
                if not p_instance != get_instance:
                    continue
            instances.append(p_instance)
        instance_details = []
        for c_instance in instances:
            hesitations = database.get_all_hesitation_reasons_for_dubious_id(instance.id, [c_instance.id])
            hesitations = [c for c in hesitations if c.reason is not None]
            c_instance_details = c_instance.get_details()
            if len(hesitations) > 0:
                c_instance_details["hesitation_reasons"] = [hesitation.reason for hesitation in hesitations]
                c_instance_details["hesitation_evidence"] = [hesitation.evidence for hesitation in hesitations if hesitation.evidence is not None]
            instance_details.append(c_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("reason", default=None, type=str, required=False, location="json")
    put_parser.add_argument("evidence", default=None, type=str, required=False, location="json")


    @api.expect(put_parser,models.input_censures_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Mistrust Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Hesitate against an instance
        A hesitation signifies a mistrust from your instance to how that instance is being run.
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can hesitation others.")
        if instance.domain == domain:
            raise e.BadRequest("You're a mad lad, but you can't hesitation yourself.")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance, nodeinfo, admin_usernames = ensure_instance_registered(domain, allow_unreachable=True)
        if not target_instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        if not target_instance:
            raise e.BadRequest("Instance to hesitation not found")
        if database.get_endorsement(target_instance.id,instance.id):
            raise e.BadRequest("You can't hesitate against an instance you've endorsed! Please withdraw the endorsement first.")
        if database.get_hesitation(target_instance.id,instance.id):
            return {"message":'OK'}, 200
    
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
        evidence = self.args.evidence
        if evidence is not None:
            evidence = sanitize_string(evidence)
        new_hesitation = Hesitation(
            hesitant_id=instance.id,
            dubious_id=target_instance.id,
            reason=reason,
            evidence=evidence,
        )
        db.session.add(new_hesitation)
        target_domain = target_instance.domain
        if instance.visibility_hesitations != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.HESITATION,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} hesitated against {domain}")
        return {"message":'Changed'}, 200

    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("reason", default=None, type=str, required=False, location="json")
    patch_parser.add_argument("evidence", default=None, type=str, required=False, location="json")


    @api.expect(patch_parser,models.input_censures_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Modify Instance Hesitation')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def patch(self, domain):
        '''Modify an instance's Hesitation
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
            raise e.BadRequest("Instance from which to modify hesitation not found")
        hesitation = database.get_hesitation(target_instance.id,instance.id)
        if not hesitation:
            raise e.BadRequest(f"No hesitation found for {domain} from {instance.domain}")
        changed = False
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
            if hesitation.reason != reason:
                hesitation.reason = reason
                changed = True
        evidence = self.args.evidence
        if evidence is not None:
            evidence = sanitize_string(evidence)
            if hesitation.evidence != evidence:
                hesitation.evidence = evidence
                changed = True
        if changed is False:
            return {"message":'OK'}, 200
        target_domain = target_instance.domain
        if instance.visibility_hesitations != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.HESITATION,
            report_activity=enums.ReportActivity.MODIFIED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} modIfied hesitation for {domain}")
        return {"message":'Changed'}, 200

    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Withdraw Instance Hesitation')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def delete(self,domain):
        '''Withdraw an instance hesitation
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
            raise e.BadRequest("Instance from which to withdraw hesitation not found")
        hesitation = database.get_hesitation(target_instance.id,instance.id)
        if not hesitation:
            return {"message":'OK'}, 200
        db.session.delete(hesitation)
        target_domain = target_instance.domain
        if instance.visibility_hesitations != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.HESITATION,
            report_activity=enums.ReportActivity.DELETED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Withdrew hesitation from {domain}")
        return {"message":'Changed'}, 200
