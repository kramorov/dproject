# 1. Читаем файл и загружаем переменные в окружение PowerShell
Get-Content "D:\drf\drf-docker.env" | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $key = $Matches[1].Trim()
        $value = $Matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value)
    }
}

# 2. Выполняем авторизацию через безопасный пайплайн с очисткой данных
$env:KEY_SECRET | docker login drf-front.cr.cloud.ru -u "$env:KEY_ID" --password-stdin
