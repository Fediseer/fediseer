from fediseer.fediverse import InstanceInfo
from fediseer.database import functions as database
from fediseer.classes.instance import Instance
from fediseer.flask import db
import fediseer.exceptions as e
from datetime import datetime
from loguru import logger

def ensure_instance_registered(domain, allow_unreachable=False, record_unreachable = False, allowed_timeout=5):
    instance = database.find_instance_by_domain(domain)
    try:
        instance_info = InstanceInfo(domain,allow_unreachable=allow_unreachable, req_timeout=allowed_timeout)
        instance_info.get_instance_info()
    except Exception as err:
        if record_unreachable and instance and instance.software != "wildcard":
            # We only consider an instance unreachable if we can't reach its nodeinfo
            # This means that a misconfigured instance will also be considered as 'down'
            if instance_info.node_info is None:
                logger.warning(f"Recorded {domain} as unreachable.")
                instance.updated = datetime.utcnow()
                if instance_info.domain_exists():
                    instance.poll_failures += 1
                else:
                    instance.poll_failures += 60
                db.session.commit()
        if not allow_unreachable:
            raise e.BadRequest(f"Error encountered while polling domain {domain}. Please check it's running correctly")
    if instance:
        if (
            instance.software != instance_info.software or
            instance.open_registrations != instance_info.open_registrations or
            instance.approval_required != instance_info.approval_required or
            instance.email_verify != instance_info.email_verify or
            instance.has_captcha != instance_info.has_captcha or
            instance.poll_failures > 0
        ):
            # logger.debug(["new",instance_info.software,instance_info.open_registrations,instance_info.approval_required,instance_info.email_verify,instance_info.has_captcha])        
            # logger.debug(["old", instance.software,instance.open_registrations,instance.approval_required,instance.email_verify,instance.has_captcha])        
            logger.debug(f"Updated instance info for {domain}")
            instance.software = instance_info.software
            instance.open_registrations = instance_info.open_registrations
            instance.approval_required = instance_info.approval_required
            instance.email_verify = instance_info.email_verify
            instance.has_captcha = instance_info.has_captcha
            instance.updated = datetime.utcnow()
            instance.poll_failures = 0
            db.session.commit()
        return instance, instance_info
    poll_failures = 0
    if not instance_info.domain_exists():
        # If the domain is gone, we assume straight decommission
        poll_failures = 100
    new_instance = Instance(
        domain=domain,
        open_registrations=instance_info.open_registrations,
        email_verify=instance_info.email_verify,
        approval_required=instance_info.approval_required,
        has_captcha=instance_info.has_captcha,
        software=instance_info.software,
        poll_failures=poll_failures,
    )
    new_instance.create()
    return new_instance, instance_info