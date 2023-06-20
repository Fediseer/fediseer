from flask_restx import fields

class Models:
    def __init__(self,api):
        self.response_model_error = api.model('RequestError', {
            'message': fields.String(description="The error message for this status code."),
        })
        self.response_model_suspicious_instances = api.model('SuspiciousInstances', {
            'domain': fields.String(description="The instance domain"),
            'uptime_alltime': fields.Float(description="The instance uptime pct. 100% and thousand of users is unlikely"),
            'local_posts': fields.Integer(description="The amount of local posts in that instance"),
            'total_users': fields.Integer(description="The total amount of users registered in that instance"),
            'active_users_monthly': fields.Integer(description="The amount of active users monthly."),
            'signup': fields.Boolean(default=False,description="True when subscriptions are open, else False"),
            'user_post_ratio': fields.Float(description="Users to Post Ratio"),
        })
        self.input_model_SusInstances_post = api.model('SuspiciousInstancesListInput', {
            'user_to_post_ratio': fields.Integer(default=20,description="The threshold over which to consider instances suspicious."),
            'whitelist': fields.List(fields.String(description="List of domains to avoid returning in the supicion list.")),
            'blacklist': fields.List(fields.String(description="List of domains to append to the supicion list.")),
        })
        self.response_model_model_SusInstances_post = api.model('SuspiciousInstancesDomainList', {
            'domains': fields.List(fields.String(description="The domains in shit suspicious list.")),
        })
