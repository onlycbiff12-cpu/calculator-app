' Calculator launcher: opens calculator.py with pythonw (no console window).
' Works from any folder: resolves its own location, so it survives moving the project.
Option Explicit

Dim fso, shell, scriptDir, target, pythonw

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
target = fso.BuildPath(scriptDir, "calculator.py")

pythonw = "C:\Users\eng-7\AppData\Local\Microsoft\WindowsApps\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

shell.CurrentDirectory = scriptDir
shell.Run """" & pythonw & """ """ & target & """", 0, False

