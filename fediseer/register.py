from fediseer.fediverse import InstanceInfo
from fediseer.database import functions as database
from fediseer.classes.instance import Instance
from fediseer.flask import db
from loguru import logger

def ensure_instance_registered(domain, allow_unreachable=False):        
    instance_info = InstanceInfo(domain,allow_unreachable=allow_unreachable)
    instance = database.find_instance_by_domain(domain)
    if instance:
        if (
            instance.software != instance_info.software or
            instance.open_registrations != instance_info.open_registrations or
            instance.approval_required != instance_info.approval_required or
            instance.email_verify != instance_info.email_verify or
            instance.has_captcha != instance_info.has_captcha
        ):
            # logger.debug(["new",instance_info.software,instance_info.open_registrations,instance_info.approval_required,instance_info.email_verify,instance_info.has_captcha])        
            # logger.debug(["old", instance.software,instance.open_registrations,instance.approval_required,instance.email_verify,instance.has_captcha])        
            logger.debug(f"Updated instance info for {domain}")
            instance.software = instance_info.software
            instance.open_registrations = instance_info.open_registrations
            instance.approval_required = instance_info.approval_required
            instance.email_verify = instance_info.email_verify
            instance.has_captcha = instance_info.has_captcha
            db.session.commit()
        
        return instance, instance_info
    new_instance = Instance(
        domain=domain,
        open_registrations=instance_info.open_registrations,
        email_verify=instance_info.email_verify,
        approval_required=instance_info.approval_required,
        has_captcha=instance_info.has_captcha,
        software=instance_info.software,
    )
    new_instance.create()
    return new_instance, instance_info
