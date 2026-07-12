$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$assetDir = Join-Path $PSScriptRoot "assets"
$audioDir = Join-Path $PSScriptRoot "audio-v2"
$kokoroPython = Join-Path $root ".ai_company\venvs\kokoro\Scripts\python.exe"
$kokoroRunner = Join-Path $root "scripts\kokoro_tts_runner.py"
New-Item -ItemType Directory -Force $assetDir, $audioDir | Out-Null

$assetUrls = @(
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4704690/6c0a47cc2fba1b160901d1553637a764198bdc98/ss_6c0a47cc2fba1b160901d1553637a764198bdc98.1920x1080.jpg?t=1782561846",
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4704690/0383a711ed93bf8edd848df4b63b331fc44f3ad5/ss_0383a711ed93bf8edd848df4b63b331fc44f3ad5.1920x1080.jpg?t=1782561846",
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4704690/51b0a906d1767b1b5abde623350dec64c6877c93/ss_51b0a906d1767b1b5abde623350dec64c6877c93.1920x1080.jpg?t=1782561846",
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4704690/0a8a562016b13a349349e685f7a4d5a6cbccef3e/ss_0a8a562016b13a349349e685f7a4d5a6cbccef3e.1920x1080.jpg?t=1782561846",
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4704690/2764a4a42c24a88d0bbb9b67e5c2bde979a24ac9/ss_2764a4a42c24a88d0bbb9b67e5c2bde979a24ac9.1920x1080.jpg?t=1782561846",
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4704690/c0c3ab9f5f2b41e86606a1c790fef432fe2d65cf/ss_c0c3ab9f5f2b41e86606a1c790fef432fe2d65cf.1920x1080.jpg?t=1782561846"
)

for ($index = 0; $index -lt $assetUrls.Count; $index++) {
    $destination = Join-Path $assetDir ("shot-{0:D2}.jpg" -f ($index + 1))
    Invoke-WebRequest -Uri $assetUrls[$index] -OutFile $destination
}

$brandLogo = Join-Path $root "assets\brands\fase_nova_games\profile-logo.png"
Copy-Item -LiteralPath $brandLogo -Destination (Join-Path $assetDir "profile-logo.png") -Force

$trailerUrl = "https://video.akamai.steamstatic.com/store_trailers/4704690/438048352/68ce99874351195c215dd093f02a8de3fed9ef66/1781024020/hls_264_master.m3u8?t=1781024570"
$trailerPath = Join-Path $assetDir "official-trailer-clean.mp4"
& ffmpeg -y -err_detect ignore_err -i $trailerUrl -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart $trailerPath
if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg could not prepare the official trailer."
}

if (-not (Test-Path -LiteralPath $kokoroPython)) {
    throw "Kokoro environment not found at $kokoroPython"
}

$env:PATH = "C:\Program Files\eSpeak NG;$env:PATH"
$segments = @(
    "Esse jogo de esconde-esconde... virou fenômeno na Steam! E agora, acabou de receber uma atualização bem curiosa.",
    "A versão dois ponto seis trouxe o mapa de colaboração HIKAKIN Museum — com mecânicas exclusivas dentro do mapa.",
    "A ideia é simples... e caótica: você pinta o personagem, se mistura ao cenário... e tenta enganar o caçador.",
    "Também chegou suporte para controle, em versão alfa. Mas atenção: a interface ainda não funciona pelo controle.",
    "E tem mais: novas regiões na Ásia, correções nas colisões... e o campo de visão do caçador subiu de cem para cento e cinco.",
    "Agora eu quero saber: você conseguiria desaparecer nesse cenário? Segue a Fase Nova Games para mais notícias."
)

for ($index = 0; $index -lt $segments.Count; $index++) {
    $destination = Join-Path $audioDir ("scene-{0:D2}.wav" -f ($index + 1))
    $payload = @{
        text = $segments[$index]
        voice = "pm_alex"
        speed = 1.0
        output_path = $destination
    } | ConvertTo-Json -Compress
    $result = $payload | & $kokoroPython $kokoroRunner
    if ($LASTEXITCODE -ne 0) {
        throw "Kokoro failed on scene $($index + 1): $result"
    }
}

Write-Output "Second-cut gameplay and Kokoro narration are ready."
