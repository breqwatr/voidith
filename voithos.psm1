# ps1
# Code style: https://poshcode.gitbooks.io/powershell-practice-and-style/content/Style-Guide/Code-Layout-and-Formatting.html

function Get-BootStyle {
  param(
    [Parameter(Position = 0, ValueFromPipeline = $true, ValueFromRemainingArguments = $true)]
    [string]
    $DriveLetter
  )
	begin{}
  process {
	  Write-Host "NOT IMPLEMENTED"
  }
  end {}
}

# Export the functions
Export-ModuleMember -Function Get-BootStyle
