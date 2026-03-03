# Memory MCP Entity Schema

Entity model for the Government Automation Factory, stored in Memory MCP. Created and queried by `/gov-factory:new-project` and `/gov-factory:status`.

## Entity Types

### factory_project

A project created by the factory pipeline.

| Observation | Type | Description |
|-------------|------|-------------|
| name | string | Project slug (e.g., `waterbot`) |
| track | `bot` \| `form` | Project track |
| domain | string | Domain description (e.g., "water rights permitting") |
| slug | string | Domain slug for file naming |
| status | `active` \| `deployed` \| `archived` | Project lifecycle status |
| pipeline_stage | string | Current pipeline stage (see Pipeline Stages below) |
| created_date | YYYY-MM-DD | Project creation date |
| project_dir | string | Filesystem path to project directory |
| schema_name | string | Supabase schema name |

### factory_domain

A researched government domain. Created by `/gov-factory:research-domain`.

| Observation | Type | Description |
|-------------|------|-------------|
| description | string | Domain description |
| research_depth | `quick` \| `standard` \| `deep` | Depth of Perplexity research |
| research_date | YYYY-MM-DD | Date research was conducted |
| stakeholder_brief_path | string | Path to stakeholder brief output |
| developer_assessment_path | string | Path to developer assessment output |

### factory_deployment

A deployed project instance. Created post-deploy.

| Observation | Type | Description |
|-------------|------|-------------|
| url | string | Live URL (e.g., `https://vanderdev.net/waterbot`) |
| deploy_date | YYYY-MM-DD | Deployment date |
| deploy_script_used | `deploy-bot.sh` \| `deploy-form.sh` | Which script deployed it |
| vps_host | string | VPS hostname |

## Relations

| From | Relation | To | Description |
|------|----------|----|-------------|
| factory_project | `researched_domain` | factory_domain | Project's researched domain |
| factory_project | `deployed_as` | factory_deployment | Project's deployment record |
| factory_project | `created_by` | gov_automation_factory | Factory singleton entity |

## Pipeline Stages (Ordered)

```
scaffolded → researched → decks → knowledge → ingested → building → deployed
```

| Stage | Set By | Meaning |
|-------|--------|---------|
| scaffolded | new-project Step 2 | Directory created by scaffold.sh |
| researched | new-project Step 3 | Research outputs generated |
| decks | new-project Step 4 | HTML presentations built |
| knowledge | new-project Step 5 | Knowledge docs converted |
| ingested | new-project Step 6 | RAG chunks embedded (bot only) |
| building | GSD workflow | Build phase in progress |
| deployed | deploy scripts | Live on vanderdev.net |

## Entity Naming Convention

All entity names use the pattern: `{project_slug}_{entity_type}`

- Project: `waterbot_project`
- Domain: `water-rights-permitting_domain`
- Deployment: `waterbot_deployment`
- Factory singleton: `gov_automation_factory`

Domain entities use the domain slug (from research), project entities use the project slug (from scaffold). These may differ: domain `water-rights-permitting` → project `waterbot`.

## API Examples

### Create a project entity

```json
mcp__memory__create_entities([{
  "name": "waterbot_project",
  "entityType": "factory_project",
  "observations": [
    "name: waterbot",
    "track: bot",
    "domain: water rights permitting",
    "slug: water-rights-permitting",
    "status: active",
    "pipeline_stage: scaffolded",
    "created_date: 2026-02-08",
    "project_dir: ~/Documents/GitHub/gov-ai-dev/waterbot",
    "schema_name: waterbot"
  ]
}])
```

### Add a relation to the factory singleton

```json
mcp__memory__create_relations([{
  "from": "waterbot_project",
  "to": "gov_automation_factory",
  "relationType": "created_by"
}])
```

### Link project to its researched domain

```json
mcp__memory__create_relations([{
  "from": "waterbot_project",
  "to": "water-rights-permitting_domain",
  "relationType": "researched_domain"
}])
```

### Update pipeline stage

```json
mcp__memory__add_observations([{
  "entityName": "waterbot_project",
  "contents": ["pipeline_stage: deployed", "status: deployed"]
}])
```

### Record a deployment

```json
mcp__memory__create_entities([{
  "name": "waterbot_deployment",
  "entityType": "factory_deployment",
  "observations": [
    "url: https://vanderdev.net/waterbot",
    "deploy_date: 2026-02-08",
    "deploy_script_used: deploy-bot.sh",
    "vps_host: vps"
  ]
}])

mcp__memory__create_relations([{
  "from": "waterbot_project",
  "to": "waterbot_deployment",
  "relationType": "deployed_as"
}])
```

### Query all factory projects

```json
mcp__memory__search_nodes({ "query": "factory_project" })
```

### Query a specific project

```json
mcp__memory__search_nodes({ "query": "waterbot_project" })
```

### Read full graph (all entities and relations)

```json
mcp__memory__read_graph()
```
