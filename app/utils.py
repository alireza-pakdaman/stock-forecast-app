import io, base64
def fig_to_base64(fig):
    if hasattr(fig, "to_image"):
        img_bytes = fig.to_image(format="png")
    else:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        img_bytes = buf.getvalue()
    return "data:image/png;base64," + base64.b64encode(img_bytes).decode()
