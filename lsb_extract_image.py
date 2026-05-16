from PIL import Image
from pathlib import Path
import struct
import sys

MAGIC = b"LSBIMG2"

def bits_to_byte(bits):
    v = 0
    for bit in bits:
        v = (v << 1) | bit
    return v

def extract_lsb(stego_file, output_file, bits_per_channel=2):
    stego_file = Path(stego_file)
    output_file = Path(output_file)

    img = Image.open(stego_file).convert("RGBA")
    bit_buffer = []
    out_bytes = bytearray()

    for r, g, b, a in img.getdata():
        for ch in (r, g, b):
            for i in range(bits_per_channel - 1, -1, -1):
                bit_buffer.append((ch >> i) & 1)
                if len(bit_buffer) == 8:
                    out_bytes.append(bits_to_byte(bit_buffer))
                    bit_buffer = []

    data = bytes(out_bytes)
    if not data.startswith(MAGIC):
        raise ValueError("Arquivo não contém o marcador LSBIMG2 esperado ou foi recomprimido/alterado.")

    size = struct.unpack(">I", data[len(MAGIC):len(MAGIC)+4])[0]
    start = len(MAGIC) + 4
    output_file.write_bytes(data[start:start+size])
    print(f"Imagem oculta extraída para: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Uso: python lsb_extract_image.py "imagem_final.png" "imagem_extraida.png"')
        sys.exit(1)

    extract_lsb(sys.argv[1], sys.argv[2])
