from flask_restx import fields

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
        self.response_model_instances = api.model('InstanceDetails', {
            'id': fields.Integer(description="The instance id", example=1),
            'domain': fields.String(description="The instance domain", example="lemmy.dbzer0.com"),
            'software': fields.String(description="The fediverse software running in this instance", example="lemmy"),
            'claimed': fields.Integer(description="How many admins from this instance has claimed it."),
            'open_registrations': fields.Boolean(description="The instance uptime pct. 100% and thousand of users is unlikely"),
            'email_verify': fields.Boolean(description="The amount of local posts in that instance"),
            'approvals': fields.Integer(description="The amount of endorsements this instance has given out"),
            'endorsements': fields.Integer(description="The amount of endorsements this instance has received"),
            'guarantor': fields.String(description="The domain of the instance which guaranteed this instance.", example="fediseer.com"),
            'censure_reasons': fields.List(fields.String(description="The reasons instances have given for censuring this instance")),
        })
        self.response_model_model_Whitelist_get = api.model('WhitelistedInstances', {
            'instances': fields.List(fields.Nested(self.response_model_instances)),
            'domains': fields.List(fields.String(description="The instance domains as a list.")),
            'csv': fields.String(description="The instance domains as a csv."),
        })
        self.input_censures_modify = api.model('ModifyCensure', {
            'reason': fields.String(required=False, description="The reason for this censure. No profanity or hate speech allowed!", example="csam"),
        })
        self.response_model_api_key_reset = api.model('ApiKeyReset', {
            "message": fields.String(default='OK',required=True, description="The result of this operation."),
            "new_key": fields.String(default=None,required=False, description="The new API key"),
        })
        self.input_api_key_reset = api.model('ApiKeyResetInput', {
            'admin_username': fields.String(required=False, description="If a username is given, their API key will be reset. Otherwise the user's whose API key was provided will be reset. This allows can be initiated by other instance admins or the fediseer.", example="admin"),
            'return_new_key': fields.Boolean(required=False, default=False, description="If True, the key will be returned as part of the response instead of PM'd. Fediseer will still PM a notification to the target admin account."),
        })
