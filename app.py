import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="ChronoTrack Post-Race Read Analyzer", layout="wide")
st.title("📊 ChronoTrack Post-Race Read Analyzer")

uploaded_file = st.file_uploader("Upload a raw data file (`~` delimited)", type=["txt", "csv"])

if uploaded_file:
    device_data = defaultdict(lambda: defaultdict(list))

    for line in uploaded_file:
        decoded = line.decode("utf-8").strip()
        parts = decoded.split("~")
        if len(parts) < 12:
            continue
        device = parts[6]
        port = parts[7]
        try:
            rssi = int(parts[8])
            stat = float(parts[11])
            device_data[device][port].append((rssi, stat))
        except ValueError:
            continue

    rows = []
    for device in sorted(device_data.keys()):
        total_reads = sum(len(v) for v in device_data[device].values())

        for port in sorted(device_data[device].keys(), key=lambda x: int(x)):
            entries = device_data[device][port]
            count = len(entries)
            percent = (count / total_reads) * 100 if total_reads > 0 else 0
            avg_rssi = sum(r for r, _ in entries) / count
            avg_stat = sum(s for _, s in entries) / count

            strong = [r for r, _ in entries if 0 >= r > -50]
            good = [r for r, _ in entries if -50 >= r > -65]
            weak = [r for r, _ in entries if -65 >= r >= -99]

            row = {
                "Device": device,
                "Port": port,
                "Count": count,
                "% Dev": f"{percent:.1f}%",
                "Avg RSSI": round(avg_rssi, 1),
                "Avg Stat": round(avg_stat, 1),
                "Strong": f"{len(strong)} ({(len(strong)/count)*100:.1f}%)",
                "Good": f"{len(good)} ({(len(good)/count)*100:.1f}%)",
                "Weak": f"{len(weak)} ({(len(weak)/count)*100:.1f}%)"
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # Export to TXT
    st.subheader("📤 Export Data")
    export_name = st.text_input("Filename (without extension):", value="post_race_summary")
    if st.button("Download TXT Summary"):
        lines = []
        header = (
            f"{'Device':<10} {'Port':<5} {'Count':<6} {'% Dev':<7} {'Avg RSSI':<9} {'Avg Stat':<9} "
            f"{'Strong':<13} {'Good':<13} {'Weak':<13}\n" + "-" * 105 + "\n"
        )
        lines.append(header)
        for row in rows:
            formatted = (
                f"{row['Device']:<10} {row['Port']:<5} {row['Count']:<6} {row['% Dev']:<7} "
                f"{row['Avg RSSI']:<9} {row['Avg Stat']:<9} {row['Strong']:<13} "
                f"{row['Good']:<13} {row['Weak']:<13}\n"
            )
            lines.append(formatted)

        txt_content = "".join(lines)
        st.download_button(
            label="📥 Download Summary as .txt",
            data=txt_content,
            file_name=f"{export_name}.txt",
            mime="text/plain"
        )
