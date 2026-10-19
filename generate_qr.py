import qrcode

revolut_link = "https://revolut.me/ballymoregaa"

qr = qrcode.make(revolut_link)

qr.save("revolut_qr.png")

print("QR code saved as revolut_qr.png")