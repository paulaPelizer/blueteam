from PIL import Image
from pathlib import Path
import struct
import sys

MAGIC = b"LSBIMG2"

def bytes_to_bits(data: bytes):
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1

def embed_lsb(cover_file, hidden_file, output_file, bits_per_channel=2):
    cover_file = Path(cover_file)
    hidden_file = Path(hidden_file)
    output_file = Path(output_file)

    img = Image.open(cover_file).convert("RGBA")
    pixels = list(img.getdata())
    hidden = hidden_file.read_bytes()
    payload = MAGIC + struct.pack(">I", len(hidden)) + hidden

    capacity_bits = len(pixels) * 3 * bits_per_channel
    required_bits = len(payload) * 8
    if required_bits > capacity_bits:
        raise ValueError(
            f"Imagem de cobertura sem capacidade. Precisa de {required_bits//8} bytes; "
            f"capacidade aproximada {capacity_bits//8} bytes com {bits_per_channel} bits/canal."
        )

    bit_iter = bytes_to_bits(payload)
    mask_clear = 0xFF ^ ((1 << bits_per_channel) - 1)
    new_pixels = []
    finished = False

    for r, g, b, a in pixels:
        channels = [r, g, b]
        new_channels = []
        for ch in channels:
            value = 0
            used = 0
            for _ in range(bits_per_channel):
                try:
                    value = (value << 1) | next(bit_iter)
                    used += 1
                except StopIteration:
                    finished = True
                    break
            if used == bits_per_channel:
                ch = (ch & mask_clear) | value
            elif used > 0:
                value = value << (bits_per_channel - used)
                ch = (ch & mask_clear) | value
            new_channels.append(ch)

        new_pixels.append((new_channels[0], new_channels[1], new_channels[2], a))

        if finished:
            idx = len(new_pixels)
            new_pixels.extend(pixels[idx:])
            break

    out = Image.new("RGBA", img.size)
    out.putdata(new_pixels)
    out.save(output_file, "PNG")
    print(f"Imagem gerada: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('Uso: python lsb_embed_image.py "imagem_original.png" "imagem_oculta.png" "imagem_final.png"')
        sys.exit(1)

    embed_lsb(sys.argv[1], sys.argv[2], sys.argv[3])
