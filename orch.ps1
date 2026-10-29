param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)
uv run python -m orch.cli @Args
