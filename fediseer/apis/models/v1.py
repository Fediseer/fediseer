from flask_restx import fields
from fediseer import enums

class Models:
    def __init__(self,api):
        self.response_model_error = api.model('RequestError', {
            'message': fields.String(description="The error message for this status code."),
        })
        self.response_model_simple_response = api.model('SimpleResponse', {
            "message": fields.String(default='OK',required=True, description="The result of this operation."),
        })
        self.response_model_suspicious_instances = api.model('SuspiciousInstances', {
            'domain': fields.String(description="The instance domain"),
            'uptime_alltime': fields.Float(description="The instance uptime pct. 100% and thousand of users is unlikely"),
            'local_posts': fields.Integer(description="The amount of local posts in that instance"),
            'comment_counts': fields.Integer(description="The amount of comments in that instance"),
            'total_users': fields.Integer(description="The total amount of users registered in that instance"),
            'active_users_monthly': fields.Integer(description="The amount of active users monthly."),
            'signup': fields.Boolean(default=False,description="True when subscriptions are open, else False"),
            'activity_suspicion': fields.Float(description="Local users per Comments+Posts. Higher is worse"),
            'active_users_suspicion': fields.Float(description="Local users per monthly active user. Higher is worse"),
        })
        self.response_model_model_Suspicions_get = api.model('SuspiciousInstances', {
            'instances': fields.List(fields.Nested(self.response_model_suspicious_instances)),
            'domains': fields.List(fields.String(description="The suspicious domains as a list.")),
            'csv': fields.String(description="The suspicious domains as a csv."),
        })
        self.response_model_model_Config_get = api.model('FediseerConfig', {
            'max_guarantees': fields.Integer(description="The total amount of guarantees one instance can give", required=True),
            'max_guarantors': fields.Integer(description="The total amount of guarantors one instance can have", required=True),
            'max_config_actions_per_min': fields.Integer(description="The amount of config actions one instance can take per minute.", required=True),
            'max_tags': fields.Integer(description="The maximum tags each instance can self-assign.", required=True),
        })
        self.response_model_instances = api.model('InstanceDetails', {
            'id': fields.Integer(description="The instance id", example=1),
            'domain': fields.String(description="The instance domain", example="lemmy.dbzer0.com"),
            'software': fields.String(description="The fediverse software running in this instance", example="lemmy"),
            'claimed': fields.Integer(description="How many admins from this instance has claimed it."),
            'open_registrations': fields.Boolean(description="The instance uptime pct. 100% and thousand of users is unlikely."),
            'email_verify': fields.Boolean(description="The amount of local posts in that instance."),
            'approval_required': fields.Boolean(description="Whether user registration requires admin approval."),
            'has_captcha': fields.Boolean(description="Whether user registration requires passing a captcha."),
            'approvals': fields.Integer(description="The amount of endorsements this instance has given out"),
            'endorsements': fields.Integer(description="The amount of endorsements this instance has received"),
            'guarantor': fields.String(description="The domain of the instance which guaranteed this instance.", example="fediseer.com"),
            'censure_reasons': fields.List(fields.String(description="The reasons instances have given for censuring this instance")),
            'sysadmins': fields.Integer(required=False, default=None, description="The count of system administrators in this instance as reported by its admins."),
            'moderators': fields.Integer(required=False, default=None, description="The count of community moderators in this instance as reported by its admins."),
            'state': fields.String(required=True, enum=[e.name for e in enums.InstanceState], description="The state of the instance as seen from the fediseer."),
            'tags': fields.List(fields.String(min_length=2, required=False, description="Domain tags (if any)")),

        })
        self.response_model_flag_details = api.model('FlagDetails', {
            'flag': fields.String(required=True, enum=[e.name for e in enums.InstanceFlags], description="The type of flag"),
            'comment': fields.String(required=False, description="A comment explaining this flag", example="admin"),
        })
        self.response_model_instances_visibility = api.inherit('InstanceVisibilityDetails', self.response_model_instances, {
            'visibility_endorsements': fields.String(required=True, enum=[e.name for e in enums.ListVisibility], description="If OPEN, this instance allows anyone to read this instance's endorsements. When set to ENDORSED, only endorsed instances can see their endorsements. If set to PRIVATE allow this instance's own admins can see their endorsements."),
            'visibility_censures': fields.String(required=True, enum=[e.name for e in enums.ListVisibility], description="If OPEN, this instance allows anyone to read this instance's censures. When set to ENDORSED, only endorsed instances can see their censures. If set to PRIVATE allow this instance's own admins can see their censures."),
            'visibility_hesitations': fields.String(required=True, enum=[e.name for e in enums.ListVisibility], description="If OPEN, this instance allows anyone to read this instance's hesitations. When set to ENDORSED, only endorsed instances can see their hesitations. If set to PRIVATE allow this instance's own admins can see their hesitations."),
            'flags': fields.List(fields.Nested(self.response_model_flag_details)),
        })
        self.response_model_model_Whitelist_get = api.model('WhitelistedInstances', {
            'instances': fields.List(fields.Nested(self.response_model_instances_visibility)),
            'domains': fields.List(fields.String(description="The instance domains as a list.")),
            'csv': fields.String(description="The instance domains as a csv."),
            'total': fields.Integer(description="The total amount of results in the database for this query. Use this to know the amount of pages"),
        })
        self.response_model_instances_censured = api.inherit('CensuredInstanceDetails', self.response_model_instances, {
            'censure_reasons': fields.List(fields.String(description="The reasons instances have given for censuring this instance")),
            'censure_evidence': fields.List(fields.String(description="Evidence justifying this censure, typically should be one or more URLs.")),
            'rebuttal': fields.List(fields.String(description="Counter argument by the target instance.", example="Nuh uh!")),
            'censure_count': fields.Integer(description="The amount of censures this instance has received from the reference instances"),
        })
        self.response_model_model_Censures_get = api.model('CensuredInstances', {
            'instances': fields.List(fields.Nested(self.response_model_instances_censured)),
            'domains': fields.List(fields.String(description="The instance domains as a list.")),
            'csv': fields.String(description="The instance domains as a csv."),
            'total': fields.Integer(description="The total amount of results in the database for this query. Use this to know the amount of pages"),
        })
        self.response_model_instances_endorsed = api.inherit('EndorsedInstanceDetails', self.response_model_instances, {
            'endorsement_reasons': fields.List(fields.String(description="The reasons instances have given for endorsing this instance")),
        })
        self.response_model_model_Endorsed_get = api.model('EndorsedInstances', {
            'instances': fields.List(fields.Nested(self.response_model_instances_endorsed)),
            'domains': fields.List(fields.String(description="The instance domains as a list.")),
            'csv': fields.String(description="The instance domains as a csv."),
            'total': fields.Integer(description="The total amount of results in the database for this query. Use this to know the amount of pages"),
        })
        self.response_model_dubious_instances = api.inherit('DubiousInstanceDetails', self.response_model_instances, {
            'hesitation_reasons': fields.List(fields.String(description="The reasons instances have given for hesitating against this instance")),
            'hesitation_evidence': fields.List(fields.String(description="Evidence justifying this hesitation, typically should be one or more URLs.")),
            'rebuttal': fields.List(fields.String(description="Counter argument by the target instance.", example="Nuh uh!")),
            'hesitation_count': fields.Integer(description="The amount of hesitations this instance has received from the reference instances"),
        })
        self.response_model_model_Hesitations_get = api.model('DubiousInstances', {
            'instances': fields.List(fields.Nested(self.response_model_dubious_instances)),
            'domains': fields.List(fields.String(description="The instance domains as a list.")),
            'csv': fields.String(description="The instance domains as a csv."),
            'total': fields.Integer(description="The total amount of results in the database for this query. Use this to know the amount of pages"),
        })
        self.input_endorsements_modify = api.model('ModifyEndorsements', {
            'reason': fields.String(required=False, description="The reason for this endorsement. No profanity or hate speech allowed!", example="I just think they're neat."),
        })
        self.input_censures_modify = api.model('ModifyCensureHesitations', {
            'reason': fields.String(required=False, description="The reason for this censure/hesitation. No profanity or hate speech allowed!", example="csam"),
            'evidence': fields.String(required=False, description="The evidence for this censure/hesitation. Typically URL but can be a long form of anything you feel appropriate.", example="https://link.to/your/evidence", max_length=1000),
        })
        self.input_rebuttals_modify = api.model('ModifyRebuttals', {
            'rebuttal': fields.String(required=False, description="The counter-argument for this censure/hesitation.", example="Nuh uh!", max_length=1000),
        })
        self.response_model_api_key_reset = api.model('ApiKeyReset', {
            "message": fields.String(default='OK',required=True, description="The result of this operation."),
            "new_key": fields.String(default=None,required=False, description="The new API key"),
        })
        self.input_instance_claim = api.model('ClaimInstanceInput', {
            'admin': fields.String(required=True, min_length=1, description="The username of the admin who wants to register this domain", example="admin"),
            'guarantor': fields.String(required=False, description="(Optional) The domain of the guaranteeing instance. They will receive a PM to validate you", example="lemmy.dbzer0.com"),
            'pm_proxy': fields.String(required=False, enum=[e.name for e in enums.PMProxy], description="(Optional) If you do receive the PM from @fediseer@fediseer.com, set this to 'MASTODON' to make the Fediseer PM your your API key via @fediseer@botsin.space. For this to work, ensure that botsin.space is not blocked in your instance and optimally follow @fediseer@botsin.space as well. If set, this will be used permanently for communication to your instance."),
        })
        self.input_instance_modify = api.model('InstanceModify', {
            'admin_username': fields.String(required=False, description="If a username is given, their API key will be reset. Otherwise the user's whose API key was provided will be reset. This allows can be initiated by other instance admins or the fediseer.", example="admin"),
            'return_new_key': fields.Boolean(required=False, default=False, description="If True, the key will be returned as part of the response instead of PM'd. Fediseer will still PM a notification to the target admin account."),
            'sysadmins': fields.Integer(required=False, default=None, min=0, max=100, description="Report how many system administrators this instance currently has."),
            'moderators': fields.Integer(required=False, default=None, min=0, max=1000, description="Report how many instance moderators this instance currently has."),
            'pm_proxy': fields.String(required=False, enum=[e.name for e in enums.PMProxy], description="(Optional) If you do receive the PM from @fediseer@fediseer.com, set this to 'MASTODON' to make the Fediseer PM your your API key via @fediseer@botsin.space. For this to work, ensure that botsin.space is not blocked in your instance and optimally follow @fediseer@botsin.space as well. If set, this will be used permanently for communication to your instance."),
            'visibility_endorsements': fields.String(required=False, enum=[e.name for e in enums.ListVisibility], description="Set this to OPEN, to allow anyone to read your endorsements. Set to ENDORSED to only allow endorsed instances to read your endorsements. Set to PRIVATE to only allow your own admins to read your endorsements."),
            'visibility_censures': fields.String(required=False, enum=[e.name for e in enums.ListVisibility], description="Set this to OPEN, to allow anyone to read your censures. Set to ENDORSED to only allow endorsed instances to read your censures. Set to PRIVATE to only allow your own admins to read your censures."),
            'visibility_hesitations': fields.String(required=False, enum=[e.name for e in enums.ListVisibility], description="Set this to OPEN, to allow anyone to read your hesitations. Set to ENDORSED to only allow endorsed instances to read your hesitations. Set to PRIVATE to only allow your own admins to read your hesitations."),
        })
        self.response_model_reports = api.model('ActivityReport', {
            'source_domain': fields.String(description="The instance domain which initiated this activity", example="lemmy.dbzer0.com"),
            'target_domain': fields.String(description="The instance domain which was the target of this activity", example="lemmy.dbzer0.com"),
            'report_type': fields.String(description="The type of report activity", enum=[e.name for e in enums.ReportType]),
            'report_activity': fields.String(description="The activity reported", enum=[e.name for e in enums.ReportActivity]),
            'created': fields.DateTime(description="The date this record was added"),
        })
        self.input_solicit = api.model('SolicitInput', {
            'guarantor': fields.String(required=False, description="The domain of the instance to solicit for a guarantee. They will receive a PM to guarantee for you", example="lemmy.dbzer0.com", min_length=1, max_length=255),
            'comment': fields.String(required=False, description="You can provide some info about your instance here.", example="Me No Spam!", min_length=1, max_length=1000),
        })

        self.response_model_instances_soliciting = api.inherit('SolicitingInstanceDetails', self.response_model_instances, {
            'comment': fields.String(description="The optional comment explaining why this instance deserves a guarantee"),
        })
        self.response_model_model_Solicitation_get = api.model('SolicitedInstances', {
            'instances': fields.List(fields.Nested(self.response_model_instances_soliciting)),
            'domains': fields.List(fields.String(description="The instance domains as a list.")),
            'csv': fields.String(description="The instance domains as a csv."),
        })
        self.input_flag_modify = api.model('FlagModify', {
            'flag': fields.String(required=True, enum=[e.name for e in enums.InstanceFlags], description="The type of flag to apply"),
            'comment': fields.String(max_length=255, required=False, description="A comment explaining this flag", example="reasons"),
        })
        self.input_tags = api.model('Tags', {
            'tags_csv': fields.String(min_length=2, required=True, description="A comma-separated list of tags"),
        })
        self.response_model_faq_entry = api.model('FAQEntry', {
            'category': fields.String(description="The overarching category for this entry", example="terminology"),
            'category_translated': fields.String(description="The overarching category for this entry, translated to the target language.", example="terminology"),
            'translated': fields.Boolean(description="If false, this entry has not yet been translated to the target language."),
            'added': fields.DateTime(description="The date this entry was added"),
            'question': fields.String(description="The entry in question form", example="What is an FAQ?"),
            'stub': fields.String(description="The entry in a short form", example="faq"),
            'document': fields.String(description="The answer provided by this FAQ entry", example="An FAQ stands for Frequently Asked Questions."),
        })
        self.input_batch_entry = api.inherit('BatchEntry', self.input_censures_modify, {
            'domain': fields.String(required=True, description="The domain for which this entry applies to", example="lemmy.example.com"),
        })
        self.input_batch_censures = api.model('BatchCensures', {
            'delete': fields.Boolean(required=False, default=False, description="Set to true, to delete all censures which are not in the censures list."),
            'overwrite': fields.Boolean(required=False, default=False, description="Set to true, to modify all existing entries with new data."),
            'censures': fields.List(fields.Nested(self.input_batch_entry)),
        })
        self.input_batch_endorsements_entry = api.inherit('BatchEndorsementEntry', self.input_endorsements_modify, {
            'domain': fields.String(required=True, description="The domain for which this entry applies to", example="lemmy.example.com"),
        })
        self.input_batch_endorsements = api.model('BatchEndorsements', {
            'delete': fields.Boolean(required=False, default=False, description="Set to true, to delete all endorsements which are not in the endorsements list."),
            'overwrite': fields.Boolean(required=False, default=False, description="Set to true, to modify all existing entries with new data."),
            'endorsements': fields.List(fields.Nested(self.input_batch_endorsements_entry)),
        })
        self.input_batch_hesitations = api.model('BatchHesitations', {
            'delete': fields.Boolean(required=False, default=False, description="Set to true, to delete all hesitations which are not in the hesitations list."),
            'overwrite': fields.Boolean(required=False, default=False, description="Set to true, to modify all existing entries with new data."),
            'hesitations': fields.List(fields.Nested(self.input_batch_entry)),
        })
        self.response_model_tag_info = api.model('TagsInfo', {
            'tag': fields.String(description="The tag name (lowercased)", example="anarchism"),
            'count': fields.Integer(description="The amount of instances tagged with this tag", example="5"),
        })