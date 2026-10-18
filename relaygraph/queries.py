"""Named, parameterized graph tools. Request text is never executed as Cypher."""

META = "MATCH (m:Meta {id:'root'}) RETURN m.revision, m.title, m.lastOperation"
NODES = "MATCH (n:Entity) RETURN n.id, labels(n), properties(n) ORDER BY n.id LIMIT 250"
EDGES = "MATCH (a:Entity)-[e]->(b:Entity) RETURN a.id,type(e),b.id,properties(e) LIMIT 500"
IMPACT = """
MATCH p=(t:Task)-[:DEPENDS_ON*1..6]->(r:Requirement)
WHERE r.id IN $changed
MATCH (person:Person)-[:OWNS]->(t)
RETURN DISTINCT t.id,t.title,person.name,r.id,[n IN nodes(p) | n.id]
ORDER BY t.id
"""
ARTIFACTS = """
MATCH (a:Artifact)-[:FOR_TASK]->(t:Task)
WHERE t.id IN $tasks
RETURN a.id,a.kind,a.title,a.state,t.id,a.basisRevision
ORDER BY a.id
"""
TASK_PATHS = """
MATCH p=(t:Task {id:$task})-[:DEPENDS_ON*1..6]->(r:Requirement)
MATCH (r)-[:CITED_IN]->(s:SourceRevision)
RETURN r.id,r.title,r.value,r.version,s.id,s.title,s.body,
       [n IN nodes(p) | n.id]
ORDER BY r.id,s.id
"""
REVIEW_ACTIONS = """
MATCH (a:ReviewAction)-[:TARGETS]->(t:Task)
MATCH (person:Person)-[:OWNS]->(t)
RETURN a.id,a.title,a.state,t.id,t.title,person.name,a.reason,a.sourceIds
ORDER BY a.id
"""
OPERATION = "MATCH (o:Operation {id:$id}) RETURN o.digest,o.revision"
