"""Run: python3 -m tests.test_render  (needs graphviz `dot`). No framework."""
import pathlib
import shutil
import tempfile

from tfdiagram import generate
from tfdiagram.style import accent_for, category_of, kind_label


def test_style():
    assert category_of("aws_db_instance") == "database"
    assert category_of("aws_s3_bucket") == "storage"
    assert kind_label("aws_lambda_function") == "Lambda Function"
    assert accent_for("aws_instance", [("instance", "#abcdef")]) == "#abcdef"
    print("test_render.style ok")


def test_svg():
    if not shutil.which("dot"):
        print("test_render.svg SKIPPED (no graphviz)")
        return
    sample = '''
    resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }
    resource "aws_subnet" "public" { vpc_id = aws_vpc.main.id }
    resource "aws_instance" "web" { subnet_id = aws_subnet.public.id }
    resource "aws_s3_bucket" "assets" {}
    '''
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "main.tf").write_text(sample)
        svg = generate(d, title="T", subtitle="S")
    assert svg.startswith("<svg")
    assert svg.count('filter="url(#card)"') == 2          # 2 leaf cards
    assert "marker-end=\"url(#arrow)\"" in svg or "</svg>" in svg
    assert "#f3f7ff" in svg                               # vpc tint drawn
    print("test_render.svg ok")


if __name__ == "__main__":
    test_style()
    test_svg()
