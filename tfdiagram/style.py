"""Visual vocabulary: categories, colors, human labels, containers.

Cards are colored by *category* (compute/storage/db/...) so a single-provider
diagram is still legible. ponytail: substring tables keyed on common cloud
types. Extend the tables for more services; unknown types fall back cleanly.
"""

# --- palette (Google-ish, matches the target aesthetic) ---
INK = "#202124"
MUTE = "#5f6368"
FAINT = "#9aa0a6"

CATEGORY_COLOR = {
    "compute":    "#4285f4",
    "database":   "#a142f4",
    "storage":    "#1e8e3e",
    "network":    "#f9ab00",
    "serverless": "#12b5cb",
    "dns":        "#ea4335",
    "other":      "#5f6368",
}

# (substring, category) — first match wins
CATEGORY_RULES = [
    ("lambda", "serverless"), ("function", "serverless"), ("cloud_run", "serverless"),
    ("_db", "database"), ("database", "database"), ("rds", "database"),
    ("sql", "database"), ("dynamodb", "database"), ("spanner", "database"),
    ("bigtable", "database"), ("_table", "database"),
    ("bucket", "storage"), ("_s3", "storage"), ("storage", "storage"),
    ("efs", "storage"), ("disk", "storage"), ("volume", "storage"),
    ("load_balanc", "network"), ("_lb", "network"), ("elb", "network"),
    ("alb", "network"), ("gateway", "network"), ("security_group", "network"),
    ("firewall", "network"), ("_acl", "network"), ("route_table", "network"),
    ("nat", "network"), ("router", "network"),
    ("dns", "dns"), ("route53", "dns"), ("_zone", "dns"),
    ("instance", "compute"), ("compute", "compute"), ("_vm", "compute"),
    ("container", "compute"), ("ecs", "compute"), ("eks", "compute"),
    ("node_pool", "compute"), ("autoscaling", "compute"),
]

# (substring, pretty label)
LABEL_RULES = [
    ("aws_vpc", "VPC"), ("aws_subnet", "Subnet"),
    ("aws_instance", "EC2 Instance"), ("aws_db_instance", "RDS Database"),
    ("aws_s3_bucket", "S3 Bucket"), ("aws_lambda_function", "Lambda Function"),
    ("aws_security_group", "Security Group"), ("aws_route53_zone", "Route 53 Zone"),
    ("aws_lb", "Load Balancer"), ("aws_dynamodb", "DynamoDB Table"),
    ("aws_ecs", "ECS Service"), ("aws_eks", "EKS Cluster"),
    ("aws_nat_gateway", "NAT Gateway"), ("aws_internet_gateway", "Internet Gateway"),
    ("google_compute_network", "VPC Network"), ("google_compute_subnetwork", "Subnetwork"),
    ("google_compute_instance", "Compute Instance"), ("google_storage_bucket", "Cloud Storage"),
    ("google_sql", "Cloud SQL"), ("google_cloud_run", "Cloud Run"),
    ("azurerm_virtual_network", "Virtual Network"), ("azurerm_subnet", "Subnet"),
    ("module", "Module"),
]

# attributes worth showing on a card, in priority order
ATTR_KEYS = ["cidr_block", "instance_type", "machine_type", "engine",
             "runtime", "bucket", "name", "function_name", "image", "ami"]

# containers: (level, exact types, substrings, accent, fill tint)
CONTAINERS = [
    (0, {"aws_vpc", "google_compute_network", "azurerm_virtual_network"},
     ("vpc", "virtual_network"), "#4285f4", "#f3f7ff"),
    (1, {"aws_subnet", "google_compute_subnetwork", "azurerm_subnet"},
     ("subnet", "subnetwork"), "#f9ab00", "#fff8e1"),
]


def container_level(rtype):
    for level, exact, subs, _, _ in CONTAINERS:
        if rtype in exact or any(s in rtype for s in subs):
            return level
    return None


def container_style(level):
    _, _, _, accent, fill = CONTAINERS[level]
    return accent, fill


def category_of(rtype):
    for sub, cat in CATEGORY_RULES:
        if sub in rtype:
            return cat
    return "other"


def accent_for(rtype, overrides=()):
    for sub, hexv in overrides:
        if sub in rtype:
            return hexv
    return CATEGORY_COLOR[category_of(rtype)]


def kind_label(rtype):
    for sub, label in LABEL_RULES:
        if sub in rtype:
            return label
    # fallback: drop provider prefix, title-case
    parts = rtype.split("_")[1:] or rtype.split("_")
    return " ".join(p.capitalize() for p in parts)


def key_attr(attrs):
    for k in ATTR_KEYS:
        if k in attrs:
            return f"{k.replace('_', ' ')}: {attrs[k]}"
    return None
