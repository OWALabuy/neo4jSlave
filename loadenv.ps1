# 读取.env文件并设置环境变量(windows专用)
Get-Content .env | ForEach-Object {
    $line = $_.Trim()
    # 跳过注释和空行
    if (-not $line.StartsWith('#') -and $line -match '^(?<key>[^=]+)=(?<value>.*)$') {
        $key = $matches['key'].Trim()
        $value = $matches['value'].Trim()
        # 设置环境变量（仅当前会话有效）
        [Environment]::SetEnvironmentVariable($key, $value, 'Process')
        Write-Host "设置环境变量: $key=$value"
    }
}