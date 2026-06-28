"""Run: python3 -m tests.test_parser  (from repo root). No framework."""
import pathlib
import tempfile

from tfdiagram.parser import scan

SAMPLE = '''
resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }
resource "aws_subnet" "public" { vpc_id = aws_vpc.main.id }
resource "aws_instance" "web" {
  subnet_id     = aws_subnet.public.id
  instance_type = "t3.micro"
}
resource "aws_db_instance" "db" { db_subnet_group_name = aws_subnet.public.id }
resource "aws_s3_bucket" "assets" { bucket = "my-assets" }
module "alb" { source = "./alb"; instance = aws_instance.web.id }
'''


def test():
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "main.tf").write_text(SAMPLE)
        g = scan(d)

    assert set(g.nodes) == {
        "aws_vpc.main", "aws_subnet.public", "aws_instance.web",
        "aws_db_instance.db", "aws_s3_bucket.assets", "module.alb"}, g.nodes

    # containment
    assert g.nodes["aws_subnet.public"].parent == "aws_vpc.main"
    assert g.nodes["aws_instance.web"].parent == "aws_subnet.public"
    assert g.nodes["aws_db_instance.db"].parent == "aws_subnet.public"
    assert g.nodes["aws_s3_bucket.assets"].parent is None
    assert g.nodes["aws_vpc.main"].is_container

    # attrs
    assert g.nodes["aws_instance.web"].attrs.get("instance_type") == "t3.micro"
    assert g.nodes["aws_vpc.main"].attrs.get("cidr_block") == "10.0.0.0/16"

    # a non-containment edge survives
    assert ("aws_instance.web", "module.alb") in g.edges
    print("test_parser ok")


if __name__ == "__main__":
    test()
