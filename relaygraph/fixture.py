"""Synthetic domain fixture, authored during Graph Hacks on 2026-10-18."""

NOTICE_1 = (
    "SYNTHETIC TEST NOTICE - Campus makers showcase. Registration closes "
    "2026-10-20 18:00 Asia/Shanghai. Submit the registration form. "
    "Accessibility walkthrough remains in Room A. Not an actual event."
)


def fixture():
    nodes = [
        ('Person', {'id': 'mina', 'title': 'Mina', 'name': 'Mina', 'synthetic': True}),
        ('Person', {'id': 'noor', 'title': 'Noor', 'name': 'Noor', 'synthetic': True}),
        ('Person', {'id': 'kai', 'title': 'Kai', 'name': 'Kai', 'synthetic': True}),
        ('Person', {'id': 'jules', 'title': 'Jules', 'name': 'Jules', 'synthetic': True}),
        ('SourceRevision', {'id': 'notice_v1', 'title': 'Original notice · v1', 'body': NOTICE_1, 'revision': 1, 'synthetic': True}),
        ('Requirement', {'id': 'deadline', 'title': 'Registration deadline', 'value': '2026-10-20T18:00:00+08:00', 'version': 1}),
        ('Requirement', {'id': 'registration_form', 'title': 'Registration form', 'value': 'Registration form', 'version': 1}),
        ('Requirement', {'id': 'venue', 'title': 'Walkthrough venue', 'value': 'Room A', 'version': 1}),
        ('Task', {'id': 'register', 'title': 'Register the showcase', 'state': 'current'}),
        ('Task', {'id': 'travel', 'title': 'Confirm travel after registration', 'state': 'current'}),
        ('Task', {'id': 'catering', 'title': 'Finalize catering after travel', 'state': 'current'}),
        ('Task', {'id': 'accessibility', 'title': 'Check accessible route in Room A', 'state': 'current'}),
        ('Artifact', {'id': 'ack_register', 'title': 'Registration checklist confirmed', 'kind': 'acknowledgement', 'state': 'confirmed', 'basisRevision': 1}),
        ('Artifact', {'id': 'receipt_register', 'title': 'SYNTHETIC registration receipt', 'kind': 'receipt', 'state': 'recorded', 'basisRevision': 1}),
        ('Artifact', {'id': 'ack_travel', 'title': 'Travel plan confirmed', 'kind': 'acknowledgement', 'state': 'confirmed', 'basisRevision': 1}),
        ('Artifact', {'id': 'ack_catering', 'title': 'Catering plan confirmed', 'kind': 'acknowledgement', 'state': 'confirmed', 'basisRevision': 1}),
        ('Artifact', {'id': 'ack_accessibility', 'title': 'Accessible route confirmed', 'kind': 'acknowledgement', 'state': 'confirmed', 'basisRevision': 1}),
    ]
    edges = [
        ('mina', 'OWNS', 'register'), ('noor', 'OWNS', 'travel'),
        ('jules', 'OWNS', 'catering'), ('kai', 'OWNS', 'accessibility'),
        ('register', 'DEPENDS_ON', 'deadline'),
        ('register', 'DEPENDS_ON', 'registration_form'),
        ('travel', 'DEPENDS_ON', 'register'),
        ('catering', 'DEPENDS_ON', 'travel'),
        ('accessibility', 'DEPENDS_ON', 'venue'),
        ('deadline', 'CITED_IN', 'notice_v1'),
        ('registration_form', 'CITED_IN', 'notice_v1'),
        ('venue', 'CITED_IN', 'notice_v1'),
        ('ack_register', 'FOR_TASK', 'register'),
        ('receipt_register', 'FOR_TASK', 'register'),
        ('ack_travel', 'FOR_TASK', 'travel'),
        ('ack_catering', 'FOR_TASK', 'catering'),
        ('ack_accessibility', 'FOR_TASK', 'accessibility'),
    ]
    return nodes, edges
