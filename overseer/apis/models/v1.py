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
        self.response_model_model_SusInstances_get = api.model('SuspiciousInstancesDomainList', {
            'instances': fields.List(fields.Nested(self.response_model_suspicious_instances)),
            'domains': fields.List(fields.String(description="The suspicious domains as a list.")),
            'csv': fields.String(description="The suspicious domains as a csv."),
        })
