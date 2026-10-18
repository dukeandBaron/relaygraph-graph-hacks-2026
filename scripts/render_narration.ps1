param([string]$InputJson,[string]$OutputDirectory)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$synth=[System.Speech.Synthesis.SpeechSynthesizer]::new()
$voices=@($synth.GetInstalledVoices() | Where-Object {$_.VoiceInfo.Culture.Name -eq 'en-US'})
if($voices.Count -eq 0){throw 'No installed English voice; use the caption-only video path.'}
$synth.SelectVoice($voices[0].VoiceInfo.Name)
$synth.Rate=0
$entries=[System.IO.File]::ReadAllText($InputJson,[System.Text.Encoding]::UTF8)|ConvertFrom-Json
$output=[System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($output)|Out-Null
foreach($entry in $entries){
 $name=([string]$entry.id)+'.wav'
 $path=[System.IO.Path]::GetFullPath([System.IO.Path]::Combine($output,$name))
 if(-not $path.StartsWith($output+[System.IO.Path]::DirectorySeparatorChar)){throw 'Output path leaves narration directory'}
 if([System.IO.File]::Exists($path)){throw 'Refuse to overwrite an existing narration file'}
 $synth.SetOutputToWaveFile($path)
 $synth.Speak([string]$entry.narration)
 $synth.SetOutputToNull()
}
$synth.Dispose()
[pscustomobject]@{voice=$voices[0].VoiceInfo.Name;segments=$entries.Count;mode='local_synthesized_narration'}|ConvertTo-Json -Compress
