# Week 3 Labs (OPTIONAL)

COST WARNING: S3 and DynamoDB have free tiers (small). RDS/Aurora/ElastiCache/Redshift can cost real money if left running; Aurora and ElastiCache are not free-tier friendly. Prefer RDS free-tier-eligible small instance only if your account qualifies (check current terms), single-AZ.

1. S3: create a bucket (Block Public Access on), upload files, enable versioning, overwrite a file, delete it, restore by removing the delete marker. Add a lifecycle rule (transition to IA at 30 d, expire noncurrent at 90 d).
2. Presigned URL: generate with boto3 or `aws s3 presign`, open in a browser, let it expire.
3. DynamoDB: create a table (on-demand) with pk/sk, add items, run Query vs Scan, add a GSI, enable TTL.
4. Athena (optional): upload a CSV to S3, create a table, query (a few cents).
5. RDS (optional, brief): single-AZ db.t4g.micro Postgres, connect, then delete with "skip final snapshot" (or delete snapshot).

Cleanup: empty AND delete buckets (including all versions), delete DynamoDB tables, delete RDS instances and snapshots, remove Elastic IPs, check Billing the next day.
