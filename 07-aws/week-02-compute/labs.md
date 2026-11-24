# Week 2 Labs (OPTIONAL)

COST WARNING: Lambda has a generous free tier. EC2 t3/t4g.micro may be free-tier depending on account type (check current free tier terms). ALB, NAT Gateway, Fargate and EKS are NOT free; ALB bills hourly. Do these fast and clean up the same day.

1. Lambda: console > create function (Python) > add a test event > view logs in CloudWatch. Add a function URL, call it with curl. Try changing memory and observe duration/billed duration.
2. EC2: launch one free-tier-eligible instance in the default VPC, no key pair, connect via Session Manager (needs SSM instance profile). Install nginx via user data.
3. Optional (small cost): ECS Fargate - run a public nginx image as a service with 1 task in a public subnet; view logs; then delete the service.

Cleanup checklist: terminate EC2, delete unattached EBS volumes and Elastic IPs, delete load balancers and target groups, delete ECS services/clusters, delete NAT gateways, delete Lambda function and log groups. Check Billing > Bills next day.
