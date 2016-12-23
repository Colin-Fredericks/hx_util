def insertJavascript():
    script = """<script type='text/javascript'>
        console.log('JSBridge Working');
        </script>"""
    return script

def JSAlert(myNumber):
    script = """<script type='text/javascript'>
        console.log('Alert! ' + """ + str(myNumber) + """);
        </script>"""
    return script