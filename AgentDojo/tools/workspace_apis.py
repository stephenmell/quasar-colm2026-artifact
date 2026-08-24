import agentdojo.default_suites.v1.tools.cloud_drive_client as cloud_drive_client
import agentdojo.default_suites.v1.tools.email_client as email_client
import agentdojo.default_suites.v1.tools.calendar_client as calendar_client
import agentdojo.default_suites.v1.tools.types as agentdojo_types

TOOLS = {
        "send_email": email_client.send_email,
        "delete_email": email_client.delete_email,
        "get_unread_emails": email_client.get_unread_emails,
        "get_sent_emails": email_client.get_sent_emails,
        "get_received_emails": email_client.get_received_emails,
        "get_draft_emails": email_client.get_draft_emails,
        "search_emails": email_client.search_emails,
        "search_contacts_by_name": email_client.search_contacts_by_name,
        "search_contacts_by_email": email_client.search_contacts_by_email,
        "get_current_day": calendar_client.get_current_day,
        "search_calendar_events": calendar_client.search_calendar_events,
        "get_day_calendar_events": calendar_client.get_day_calendar_events,
        "create_calendar_event": calendar_client.create_calendar_event,
        "cancel_calendar_event": calendar_client.cancel_calendar_event,
        "reschedule_calendar_event": calendar_client.reschedule_calendar_event,
        "add_calendar_event_participants": calendar_client.add_calendar_event_participants,
        "append_to_file": cloud_drive_client.append_to_file,
        "search_files_by_filename": cloud_drive_client.search_files_by_filename,
        "create_file": cloud_drive_client.create_file,
        "delete_file": cloud_drive_client.delete_file,
        "get_file_by_id": cloud_drive_client.get_file_by_id,
        "list_files": cloud_drive_client.list_files,
        "share_file": cloud_drive_client.share_file,
        "search_files": cloud_drive_client.search_files,
        "query_ai_assistant": None,
}