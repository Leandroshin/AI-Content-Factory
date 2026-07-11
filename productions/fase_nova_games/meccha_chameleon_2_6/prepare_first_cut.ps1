$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$assetDir = Join-Path $PSScriptRoot "assets"
$audioDir = Join-Path $PSScriptRoot "audio"
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

Add-Type -AssemblyName System.Speech
$segments = @(
    "O jogo de esconde-esconde que virou fenômeno na Steam acabou de receber uma atualização bem curiosa.",
    "A versão dois ponto seis adicionou o mapa de colaboração HIKAKIN Museum, com mecânicas exclusivas dentro do mapa.",
    "Aqui, você pinta o próprio personagem para se misturar ao cenário, se esconder e enganar o caçador.",
    "O jogo também ganhou suporte para controle em versão alfa, mas a interface ainda não pode ser controlada por ele.",
    "A atualização adicionou regiões para Japão, Coreia do Sul e Leste Asiático, corrigiu colisões e aumentou o campo de visão do caçador.",
    "Você jogaria um esconde-esconde em que precisa pintar o personagem para desaparecer no cenário? Segue a Fase Nova Games para mais notícias."
)

for ($index = 0; $index -lt $segments.Count; $index++) {
    $synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synthesizer.SelectVoice("Microsoft Daniel")
    $synthesizer.Rate = 3
    $destination = Join-Path $audioDir ("scene-{0:D2}.wav" -f ($index + 1))
    $synthesizer.SetOutputToWaveFile($destination)
    $synthesizer.Speak($segments[$index])
    $synthesizer.Dispose()
}

Write-Output "First-cut assets and temporary narration are ready."
