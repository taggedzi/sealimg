#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Repo
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$script:GhCmd = $null

function Resolve-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $defaultPath = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $defaultPath) {
        return $defaultPath
    }

    throw "GitHub CLI (gh) is not installed or not on PATH. Install gh, run 'gh auth login', then re-run this script."
}

function Invoke-Gh {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    & $script:GhCmd @Args
    if ($LASTEXITCODE -ne 0) {
        throw "gh command failed with exit code ${LASTEXITCODE}: gh $($Args -join ' ')"
    }
}

function Get-Repo {
    param([string]$InputRepo)
    if ($InputRepo) {
        return $InputRepo
    }
    $resolved = Invoke-Gh repo view --json nameWithOwner -q .nameWithOwner
    if (-not $resolved) {
        throw "Could not resolve repository from current directory. Pass -Repo OWNER/REPO."
    }
    return $resolved.Trim()
}

function Label-Exists {
    param(
        [string]$RepoName,
        [string]$Name
    )
    $names = Invoke-Gh label list --repo $RepoName --limit 500 --search $Name --json name -q ".[].name"
    if (-not $names) {
        return $false
    }
    return ($names -split "`n") -contains $Name
}

function Create-Label {
    param(
        [string]$RepoName,
        [string]$Name,
        [string]$Color,
        [string]$Description
    )
    if (Label-Exists -RepoName $RepoName -Name $Name) {
        Write-Host "Label exists: $Name"
    } else {
        Invoke-Gh label create $Name --repo $RepoName --color $Color --description $Description | Out-Null
        Write-Host "Created label: $Name"
    }
}

function Milestone-Exists {
    param(
        [string]$RepoName,
        [string]$Title
    )
    $titles = Invoke-Gh api "repos/$RepoName/milestones" --paginate --jq '.[].title'
    if (-not $titles) {
        return $false
    }
    return ($titles -split "`n") -contains $Title
}

function Create-Milestone {
    param(
        [string]$RepoName,
        [string]$Title,
        [string]$Description
    )
    if (Milestone-Exists -RepoName $RepoName -Title $Title) {
        Write-Host "Milestone exists: $Title"
    } else {
        Invoke-Gh api "repos/$RepoName/milestones" --method POST -f title=$Title -f description=$Description | Out-Null
        Write-Host "Created milestone: $Title"
    }
}

function Issue-Exists {
    param(
        [string]$RepoName,
        [string]$Title
    )
    $results = Invoke-Gh issue list --repo $RepoName --search "in:title `"$Title`"" --state all --json title -q '.[].title'
    if (-not $results) {
        return $false
    }
    return ($results -split "`n") -contains $Title
}

function Create-EpicIssue {
    param(
        [string]$RepoName,
        [string]$Title,
        [string]$Labels,
        [string]$Milestone,
        [string]$Body
    )
    if (Issue-Exists -RepoName $RepoName -Title $Title) {
        Write-Host "Issue exists: $Title"
    } else {
        Invoke-Gh issue create --repo $RepoName --title $Title --label $Labels --milestone $Milestone --body $Body | Out-Null
        Write-Host "Created issue: $Title"
    }
}

$script:GhCmd = Resolve-Gh
$RepoName = Get-Repo -InputRepo $Repo

Write-Host "Bootstrapping GitHub project metadata for $RepoName"

# Labels
Create-Label -RepoName $RepoName -Name "epic" -Color "5319E7" -Description "Multi-issue initiative"
Create-Label -RepoName $RepoName -Name "backend" -Color "0052CC" -Description "Core implementation and services"
Create-Label -RepoName $RepoName -Name "cli" -Color "1D76DB" -Description "Command line behavior and UX"
Create-Label -RepoName $RepoName -Name "crypto" -Color "B60205" -Description "Cryptography and key management"
Create-Label -RepoName $RepoName -Name "metadata" -Color "0E8A16" -Description "IPTC/XMP/C2PA metadata handling"
Create-Label -RepoName $RepoName -Name "c2pa" -Color "0366D6" -Description "C2PA/JUMBF embedding and provenance"
Create-Label -RepoName $RepoName -Name "testing" -Color "FBCA04" -Description "Tests, fixtures, and QA"
Create-Label -RepoName $RepoName -Name "docs" -Color "0075CA" -Description "Documentation changes"
Create-Label -RepoName $RepoName -Name "security" -Color "D93F0B" -Description "Security and hardening"
Create-Label -RepoName $RepoName -Name "platform" -Color "C5DEF5" -Description "Cross-platform behavior"
Create-Label -RepoName $RepoName -Name "v0.1" -Color "A2EEEF" -Description "Roadmap v0.1 scope"
Create-Label -RepoName $RepoName -Name "v0.3" -Color "BFD4F2" -Description "Roadmap v0.3 scope"
Create-Label -RepoName $RepoName -Name "v0.5" -Color "D4C5F9" -Description "Roadmap v0.5 scope"
Create-Label -RepoName $RepoName -Name "v0.7" -Color "F9D0C4" -Description "Roadmap v0.7 scope"
Create-Label -RepoName $RepoName -Name "v1.0" -Color "F9F2C4" -Description "Roadmap v1.0 scope"

# Milestones
Create-Milestone -RepoName $RepoName -Title "v0.1 MVP" -Description "Initial CLI and provenance pipeline for PNG/JPEG."
Create-Milestone -RepoName $RepoName -Title "v0.3 Embedding + Batch" -Description "Best-effort C2PA embedding plus batch/watch workflow."
Create-Milestone -RepoName $RepoName -Title "v0.5 Watermark + Timestamp" -Description "Invisible watermark and public timestamp helper."
Create-Milestone -RepoName $RepoName -Title "v0.7 Expanded Formats" -Description "AVIF/HEIC/JPEG XL and advanced fingerprinting."
Create-Milestone -RepoName $RepoName -Title "v1.0 GUI" -Description "Local GUI and integration docs."

# Epics
Create-EpicIssue -RepoName $RepoName `
    -Title "epic: bootstrap python project and delivery pipeline" `
    -Labels "epic,backend,platform,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Stand up Python project layout for library + CLI, CI baseline for Windows/Linux, and fixture conventions. See docs/github-issues-plan.md (Epic 1)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: implement config and manifest domain models" `
    -Labels "epic,backend,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Implement config and manifest models, schema validation, image IDs, and profile precedence. See docs/github-issues-plan.md (Epic 2)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: key management and signing verification" `
    -Labels "epic,crypto,security,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Implement keygen/sign/verify with native crypto plus optional GPG interop path. See docs/github-issues-plan.md (Epic 3)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: implement png/jpeg pipeline and metadata writing" `
    -Labels "epic,metadata,backend,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Build PNG/JPEG processing, IPTC/XMP writing, pixel-preserving master, and web export. See docs/github-issues-plan.md (Epic 4)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: generate manifest hashes and provenance package outputs" `
    -Labels "epic,backend,cli,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Generate hashes, manifest/signature outputs, README/ZIP packaging. See docs/github-issues-plan.md (Epic 5)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: implement sidecar-first c2pa embedding strategy" `
    -Labels "epic,c2pa,metadata,v0.3" `
    -Milestone "v0.3 Embedding + Batch" `
    -Body "Always emit sidecars; best-effort PNG/JPEG embedding with non-blocking fallback. See docs/github-issues-plan.md (Epic 6)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: implement cli commands and exit code contract" `
    -Labels "epic,cli,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Implement command surface and deterministic exit code behavior. See docs/github-issues-plan.md (Epic 7)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: implement test plan and quality gates" `
    -Labels "epic,testing,security,platform,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Implement functional/mutation/security/regression test coverage. See docs/github-issues-plan.md (Epic 8)."

Create-EpicIssue -RepoName $RepoName `
    -Title "epic: finalize documentation for first release" `
    -Labels "epic,docs,v0.1" `
    -Milestone "v0.1 MVP" `
    -Body "Replace placeholders and align docs with implemented behavior. See docs/github-issues-plan.md (Epic 9)."

Write-Host "Bootstrap complete."
