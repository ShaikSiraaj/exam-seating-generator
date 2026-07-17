import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('shaiksiraaj052@gmail.com', 'qmspirygasjbbnir')
print("Login OK")
server.quit()