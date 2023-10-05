#!/usr/bin/env bash

status=0

echo -n "Account ID uniqueness check: "
duplicates=$(yq \
  'collect (.[] as $entry | $entry.accounts[] | {"name": $entry.name, "account": .})
  | group_by(.account)
  | filter(length > 1)
  | .[]
  | (.[0].account + " duplicated in " + (collect(.[].name) | join(", ")))' accounts.yaml)

if [[ -n $duplicates ]]
then
    echo "Error"
    echo "$duplicates"
    status=$(($status + 1))
else
    echo "Ok"
fi

echo -n "Schema validation: "
validation=$(check-jsonschema --output-format text --color never --schemafile schema.json <(yq --output-format json accounts.yaml))
if [[ $? -ne 0 ]]
then
    echo "Error"
    echo "$validation"
    status=$(($status + 1))
else
    echo "Ok"
fi

exit $status
