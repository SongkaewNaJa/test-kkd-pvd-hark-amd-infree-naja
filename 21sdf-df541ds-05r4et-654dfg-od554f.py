import discord
import random
import string
import json
import aiohttp
import base64
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from discord import app_commands
import asyncio
import time
import itertools
import sys
import os
from dotenv import load_dotenv

# เริ่มต้นตัวแปรต่างๆ
spinner_running = True
last_reset_time = {}
COOLDOWN_SECONDS = 300  # 5 นาที

load_dotenv()

token = os.getenv("DISCORD_TOKEN")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_FILE_URL = os.getenv("GITHUB_FILE_URL")

def generate_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

async def fetch_github_data():
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            async with session.get(GITHUB_FILE_URL, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"❌ GitHub API Error: {resp.status}")
                    return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None

async def update_github_data(new_data_encoded):
    current_data = await fetch_github_data()
    if current_data is None:
        print("❌ ไม่สามารถดึงข้อมูลจาก GitHub ได้")
        return False

    sha = current_data.get("sha", "")
    if not sha:
        print("❌ ไม่พบค่า SHA ของไฟล์ใน GitHub")
        return False

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "message": "Update HWID data",
            "content": new_data_encoded,
            "sha": sha
        }
        async with session.put(GITHUB_FILE_URL, headers=headers, json=payload) as resp:
            if resp.status in [200, 201]:
                print("✅ อัปเดตข้อมูลสำเร็จ!")
                return True
            else:
                print(f"❌ อัปเดตข้อมูลไม่สำเร็จ: {resp.status}")
                return False

# กำหนดคำสั่งที่บอทจะใช้
intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='/', intents=intents)

async def spinning_cursor():
    while spinner_running:
        for cursor in itertools.cycle(['|', '/', '-', '\\']):
            if not spinner_running:
                break
            sys.stdout.write(f'\r⌛ กำลังทำงาน... {cursor}')
            sys.stdout.flush()
            await asyncio.sleep(0.1)

@bot.tree.command(name="setup", description="สร้างข้อความพร้อมปุ่ม")
async def setup(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ **คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์!**", ephemeral=True)
        return

    #allowed_user_id = 1119509280480038972
    #if interaction.user.id != allowed_user_id:
        #await interaction.response.send_message("🚫 **คุณไม่มีสิทธิ์ใช้คำสั่งนี้!**", ephemeral=True)
        #return
    if not any(role.name == "AM" for role in interaction.user.roles):
        await interaction.response.send_message("🚫 **คุณไม่มีสิทธิ์ใช้คำสั่งนี้!**", ephemeral=True)
        return
    # ตกแต่ง Embed ที่ใช้แสดงผล
    embed = discord.Embed(
        title="✨ **Script All Map** ✨",
        description="เลือกใช้คำสั่งได้พร้อมลายละเอียดด้านล่าง",
        color=0x0094FF      # สีเขียว
    )
    embed.add_field(name="🎮 Get Script", value="กดปุ่มเพื่อรับสคริปต์ของคุณ", inline=False)
    embed.add_field(name="🖥️ Add HWID", value="กดปุ่มเพื่อเพิ่ม HWID", inline=False)
    embed.add_field(name="🔄 Reset HWID", value="กดปุ่มเพื่อรีเซ็ต HWID ของคุณ", inline=False)
    embed.add_field(name="ℹ️ Info", value="กดปุ่มเพื่อดูข้อมูลเพิ่มเติม", inline=False)
    embed.add_field(name="🚩 รายละเอียดเพิ่มเติม ควรอ่าน!", value=" ต้องมียศBuyerก่อนถึงจะใช้คำสั่งได้ | ถ้าบอทไม่ออนหรือไม่ทำงานโปรดทราบเเอดมินหลับอยูไม่มีใครเปิดบอท | หากมีอะไรสงสัยถามเเอดมินได้", inline=False)

    embed.set_image(url="https://i.pinimg.com/originals/2d/cb/fb/2dcbfb5e2a596669fc685b347c2c115c.gif")

    # ปุ่มต่างๆ ที่ผู้ใช้สามารถกดได้
    button1 = Button(label="🎮 Get Script", style=discord.ButtonStyle.primary)
    button2 = Button(label="🖥️ Add HWID", style=discord.ButtonStyle.primary)
    button3 = Button(label="🔄 Reset HWID", style=discord.ButtonStyle.primary)
    button4 = Button(label="ℹ️ Info", style=discord.ButtonStyle.secondary)

    # ฟังก์ชัน callback สำหรับแต่ละปุ่ม
    async def get_script_callback(interaction: discord.Interaction):
        script_message = f"""🔹 **สคริปต์ของคุณ**\n
```lua
getgenv().Key = \"{interaction.user.id}\" 
loadstring(game:HttpGet('https://raw.githubusercontent.com/xOne2/_dasd234/refs/heads/main/sdada.lua'))()
```"""
        await interaction.response.send_message(script_message, ephemeral=True)

    async def add_hwid_callback(interaction: discord.Interaction):
        if not any(role.name == "Buyer" for role in interaction.user.roles):
            await interaction.response.send_message("❌ คุณต้องมียศ 'Buyer' เพื่อใช้งานปุ่มนี้!", ephemeral=True)
            return
        
        modal = Modal(title="Add HWID")
        modal.add_item(TextInput(label="กรุณาใส่ HWID"))

        async def on_submit(modal_interaction: discord.Interaction):
            user_id = str(modal_interaction.user.id)
            hwid = modal.children[0].value.strip()

            github_content = await fetch_github_data()
            if not github_content:
                await modal_interaction.response.send_message("❌ ไม่สามารถดึงข้อมูลจาก GitHub ได้", ephemeral=True)
                return

            decoded_content = base64.b64decode(github_content["content"]).decode()

            if f'Key = "{user_id}"' in decoded_content:
                await modal_interaction.response.send_message("❌ คุณได้เพิ่ม HWID ไปแล้ว กรุณาใช้ Reset HWID!", ephemeral=True)
                return

            insert_line = f'    {{ Hwid = "{hwid}", Key = "{user_id}" , ExpiryDate = math.huge, Permanent = true }},\n'
            if "local whitelistPak = {" in decoded_content:
                new_data = decoded_content.replace("local whitelistPak = {\n", f"local whitelistPak = {{\n{insert_line}")
            else:
                new_data = f'local whitelistPak = {{\n{insert_line}}}\nreturn whitelistPak'

            encoded = base64.b64encode(new_data.encode()).decode()
            success = await update_github_data(encoded)

            if success:
                print(f"[{modal_interaction.user}] ส่ง HWID ใหม่: {hwid}")
                await modal_interaction.response.send_message(f'✅ HWID : {hwid} KEY : {user_id} ', ephemeral=True)
            else:
                await modal_interaction.response.send_message("❌ บันทึกล้มเหลว!", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    async def reset_hwid_callback(interaction: discord.Interaction):
        if not any(role.name == "Buyer" for role in interaction.user.roles):
            await interaction.response.send_message("❌ คุณต้องมียศ @Buyer  ก่อน! เพื่อใช้งานปุ่มนี้! โปรดติดต่อ แอดมิน @OneWiz ", ephemeral=True)
            return
        user_id = str(interaction.user.id)
        now = time.time()

        if user_id in last_reset_time:
            elapsed = now - last_reset_time[user_id]
            if elapsed < COOLDOWN_SECONDS:
                remaining = int(COOLDOWN_SECONDS - elapsed)
                await interaction.response.send_message(f"⏳ กรุณารออีก {remaining} วินาทีก่อนรีเซ็ต HWID ใหม่", ephemeral=True)
                return
            
        modal = Modal(title="Reset HWID")
        modal.add_item(TextInput(label="กรุณาใส่ HWID ใหม่"))

        async def on_submit(modal_interaction: discord.Interaction):
            user_id = str(modal_interaction.user.id)
            new_hwid = modal.children[0].value.strip()

            github_content = await fetch_github_data()
            if not github_content:
                await modal_interaction.response.send_message("❌ ไม่สามารถดึงข้อมูลจาก GitHub ได้", ephemeral=True)
                return

            decoded_content = base64.b64decode(github_content["content"]).decode()

            lines = decoded_content.split("\n")
            updated_lines = []
            found = False

            for line in lines:
                if f'Key = "{user_id}"' in line:
                    updated_lines.append(f'    {{ Hwid = "{new_hwid}", Key = "{user_id}", ExpiryDate = math.huge, Permanent = true }},')
                    found = True
                else:
                    updated_lines.append(line)

            if not found:
                await modal_interaction.response.send_message("❌ ไม่พบข้อมูล Key ของคุณ กรุณาใช้ Add HWID ก่อน!", ephemeral=True)
                return

            new_data = "\n".join(updated_lines)
            encoded = base64.b64encode(new_data.encode()).decode()
            success = await update_github_data(encoded)

            if success:
                print(f"[{modal_interaction.user}] รีเซ็ต HWID ใหม่เป็น: {  new_hwid}")
                last_reset_time[user_id] = time.time()
                await modal_interaction.response.send_message(f'✅ NEW_HWID : {new_hwid} KEY : {user_id}', ephemeral=True)
            else:
                await modal_interaction.response.send_message("❌ รีเซ็ตล้มเหลว!", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    async def info_callback(interaction: discord.Interaction):
        info_message = """**🔹 ข้อมูลบอท**
- ใช้สำหรับจัดการ HWID และ Key ของสคริปต์
- พัฒนาโดย MrMaxNaJa"""
        await interaction.response.send_message(info_message, ephemeral=True)

    # กำหนด callback สำหรับแต่ละปุ่ม
    button1.callback = get_script_callback
    button2.callback = add_hwid_callback
    button3.callback = reset_hwid_callback
    button4.callback = info_callback

    # เพิ่มปุ่มลงใน View
    view = View()
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)
    view.add_item(button4)

    # ส่ง Embed พร้อมปุ่ม
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="getscript", description="รับสคริปต์ของคุณ")
async def get_script_command(interaction: discord.Interaction):
    script_message = f"""🔹 **สคริปต์ของคุณ**\n
```lua
getgenv().Key = \"{interaction.user.id}\" 
loadstring(game:HttpGet('https://raw.githubusercontent.com/xOne2/_dasd234/refs/heads/main/sdada.lua'))()
```"""
    await interaction.response.send_message(script_message, ephemeral=True)


@bot.tree.command(name="addhwid", description="เพิ่ม HWID ของคุณ")
async def add_hwid_command(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์!", ephemeral=True)
        return
    if not any(role.name == "Buyer" for role in interaction.user.roles):
        await interaction.response.send_message("❌ คุณต้องมียศ 'Buyer' เพื่อใช้งานคำสั่งนี้!", ephemeral=True)
        return

    modal = Modal(title="Add HWID")
    modal.add_item(TextInput(label="กรุณาใส่ HWID"))

    async def on_submit(modal_interaction: discord.Interaction):
        user_id = str(modal_interaction.user.id)
        hwid = modal.children[0].value.strip()

        github_content = await fetch_github_data()
        if not github_content:
            await modal_interaction.response.send_message("❌ ไม่สามารถดึงข้อมูลจาก GitHub ได้", ephemeral=True)
            return

        decoded_content = base64.b64decode(github_content["content"]).decode()

        if f'Key = "{user_id}"' in decoded_content:
            await modal_interaction.response.send_message("❌ คุณได้เพิ่ม HWID ไปแล้ว กรุณาใช้ Reset HWID!", ephemeral=True)
            return

        insert_line = f'    {{ Hwid = "{hwid}", Key = "{user_id}" , ExpiryDate = math.huge, Permanent = true }},\n'
        if "local whitelistPak = {" in decoded_content:
            new_data = decoded_content.replace("local whitelistPak = {\n", f"local whitelistPak = {{\n{insert_line}")
        else:
            new_data = f'local whitelistPak = {{\n{insert_line}}}\nreturn whitelistPak'

        encoded = base64.b64encode(new_data.encode()).decode()
        success = await update_github_data(encoded)

        if success:
            print(f"[{modal_interaction.user}] ส่ง HWID ใหม่: {hwid}")
            await modal_interaction.response.send_message(f'✅ HWID : {hwid} KEY : {user_id}', ephemeral=True)
        else:
            await modal_interaction.response.send_message("❌ บันทึกล้มเหลว!", ephemeral=True)

    modal.on_submit = on_submit
    await interaction.response.send_modal(modal)


@bot.tree.command(name="resethwid", description="รีเซ็ต HWID ของคุณ")
async def reset_hwid_command(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์!", ephemeral=True)
        return
    if not any(role.name == "Buyer" for role in interaction.user.roles):
        await interaction.response.send_message("❌ คุณต้องมียศ 'Buyer' เพื่อใช้งานคำสั่งนี้!", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    now = time.time()

    if user_id in last_reset_time:
        elapsed = now - last_reset_time[user_id]
        if elapsed < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - elapsed)
            await interaction.response.send_message(f"⏳ กรุณารออีก {remaining} วินาทีก่อนรีเซ็ต HWID ใหม่", ephemeral=True)
            return

    modal = Modal(title="Reset HWID")
    modal.add_item(TextInput(label="กรุณาใส่ HWID ใหม่"))

    async def on_submit(modal_interaction: discord.Interaction):
        user_id = str(modal_interaction.user.id)
        new_hwid = modal.children[0].value.strip()

        github_content = await fetch_github_data()
        if not github_content:
            await modal_interaction.response.send_message("❌ ไม่สามารถดึงข้อมูลจาก GitHub ได้", ephemeral=True)
            return

        decoded_content = base64.b64decode(github_content["content"]).decode()

        lines = decoded_content.split("\n")
        updated_lines = []
        found = False

        for line in lines:
            if f'Key = "{user_id}"' in line:
                updated_lines.append(f'    {{ Hwid = "{new_hwid}", Key = "{user_id}", ExpiryDate = math.huge, Permanent = true }},')
                found = True
            else:
                updated_lines.append(line)

        if not found:
            await modal_interaction.response.send_message("❌ ไม่พบข้อมูล Key ของคุณ กรุณาใช้ Add HWID ก่อน!", ephemeral=True)
            return

        new_data = "\n".join(updated_lines)
        encoded = base64.b64encode(new_data.encode()).decode()
        success = await update_github_data(encoded)

        if success:
            print(f"[{modal_interaction.user}] รีเซ็ต HWID ใหม่เป็น: {new_hwid}")
            last_reset_time[user_id] = time.time()
            await modal_interaction.response.send_message(f'✅ NEW_HWID : {new_hwid} KEY : {user_id}', ephemeral=True)
        else:
            await modal_interaction.response.send_message("❌ รีเซ็ตล้มเหลว!", ephemeral=True)

    modal.on_submit = on_submit
    await interaction.response.send_modal(modal)


@bot.tree.command(name="info", description="ข้อมูลเกี่ยวกับระบบบอทนี้")
async def info_command(interaction: discord.Interaction):
    info_message = """**🔹 ข้อมูลบอท**
- ใช้สำหรับจัดการ HWID และ Key ของสคริปต์
- พัฒนาโดย MrMaxNaJa"""
    await interaction.response.send_message(info_message, ephemeral=True)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

# เริ่มการหมุนตัวบนบอท
async def main():
    spinner_thread = asyncio.create_task(spinning_cursor())
    await bot.start(token)
    print("End")

asyncio.run(main())
print("End")
