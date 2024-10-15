# Known AWS accounts

This repository contains known AWS account IDs (those used by vendors and AWS services).  

The purpose of this is so when a trust relationship or CloudTrail events show an AWS account ID that is unknown to you, you can more quickly identify the purpose of that account. This is meant to be used with tools to remove the need for manual web searches.

## Contributing

Account IDs included in this repository should be publicly documented. The reasons for this are 1) we want to ensure these account IDs are really for who they say they are 2) some companies may not want their account IDs mentioned publicly.

Some Account IDs are included without public documentation, in the following cases:
1. Account IDs that were introduced in prior versions of this data set, prior to our current inclusion criteria
2. Account IDs contributed with consent of the owning company.  

### Schema

- **name** (required): A string representing the name.
- **source** (optional): An array of unique strings. Each string should be the URL presenting evidence of ownership of the account ID.
- **accounts** (required): An array of unique strings, each a valid AWS account ID.
- **type** (optional): A string that must be `"aws"`.
- **enabled** (optional): A boolean used to indicate deprecation. Defaults to `true`. If `deprecated_date` is set, `enabled` must be `false`.
- **deprecated_date** (optional): A string in `YYYY-MM-DD` format representing the date when the item is deprecated.

## History
Started with the data from [duo-labs/cloudmapper](https://github.com/duo-labs/cloudmapper/blob/main/vendor_accounts.yaml) which originally forked data from
[dagrz/aws_pwn](https://github.com/dagrz/aws_pwn/blob/master/miscellanea/integrations.txt).
