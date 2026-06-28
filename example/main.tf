# Example: a small AWS web app — VPC, 2 subnets, ALB, EC2, RDS, S3, Lambda.
# Render: ../tfdiagram.py example -o example.svg

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.2.0/24"
}

resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id
}

resource "aws_lb" "front" {
  subnets         = [aws_subnet.public.id]
  security_groups = [aws_security_group.web.id]
}

resource "aws_instance" "web" {
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
}

resource "aws_db_instance" "db" {
  db_subnet_group_name = aws_subnet.private.id
}

resource "aws_s3_bucket" "assets" {
  bucket = "my-app-assets"
}

resource "aws_lambda_function" "thumbnailer" {
  function_name = "thumbnailer"
  s3_bucket     = aws_s3_bucket.assets.id
}

resource "aws_route53_zone" "primary" {
  name = "example.com"
}
