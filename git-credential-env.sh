#!/bin/sh
# git credential helper: answers for github.com from a .env file (GITHUB_USER, GITHUB_TOKEN).
# Called by git as:  git-credential-env.sh <env file> get|store|erase   (request on stdin)
env_file=$1
[ "$2" = get ] || exit 0
[ -f "$env_file" ] || exit 0
host=$(sed -n 's/^host=//p')
[ "$host" = github.com ] || exit 0
val() { sed -n "s/^$1=//p" "$env_file" | head -n 1 | tr -d '\r' | sed 's/^"\(.*\)"$/\1/'; }
token=$(val GITHUB_TOKEN)
[ -n "$token" ] || exit 0
printf 'username=%s\npassword=%s\n' "$(val GITHUB_USER)" "$token"
