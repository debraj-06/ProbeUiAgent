param(
  [Parameter(Mandatory=$true)]
  [string]$Url
)

.\.venv\Scripts\Activate.ps1
python main.py $Url
