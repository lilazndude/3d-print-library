Dim scriptDir, pyExe, pyScript
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
pyExe    = scriptDir & "_app\venv_win\Scripts\pythonw.exe"
pyScript = scriptDir & "_app\app.py"

' Check if server is already running
Dim running : running = False
Dim http : Set http = CreateObject("MSXML2.ServerXMLHTTP")
http.setTimeouts 500, 500, 500, 500
On Error Resume Next
http.Open "GET", "http://localhost:5000/", False
http.Send
If Err.Number = 0 And http.Status = 200 Then running = True
On Error GoTo 0

Set oShell = CreateObject("WScript.Shell")
If running Then
    oShell.Run "http://localhost:5000", 1, False
Else
    oShell.Run """" & pyExe & """ """ & pyScript & """", 0, False
End If
