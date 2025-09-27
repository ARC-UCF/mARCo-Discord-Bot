import discord
from discord import app_commands
from discord.ext import commands

ARC_SITE = "http://k4ucf.ucf.edu/"
ARC_WIKI = "https://newton.i2lab.ucf.edu/wiki/"
ARRL_POOLS = "https://www.arrl.org/question-pools"
ARRL_TECH = "https://www.arrl.org/getting-your-technician-license"
FCC_EXAMS = "https://www.fcc.gov/wireless/bureau-divisions/mobility-division/amateur-radio-service/examinations"
SHACK_SITE = "https://shack.crd.co/"
ARC_GITHUB = "https://github.com/ARC-UCF"

LINKS = {
    "Club & Wiki": [
        ("ARC @ UCF (K4UCF)", ARC_SITE),
        ("ARC/CECS Wiki (root)", ARC_WIKI),
        ("ARC SHACK ", SHACK_SITE),
        ("ARC GITHUB ", ARC_GITHUB),
    ],
    "Study & Testing": [
        ("ARC: Amateur radio testing", ARC_WIKI + "Amateur_radio_testing"),
        (
            "ARC: General study guide",
            ARC_WIKI + "Amateur_Radio_General_Element_3_(2007)",
        ),
        ("ARRL: Question pools", ARRL_POOLS),
        ("ARRL: Getting Your Technician License", ARRL_TECH),
    ],
    "Operating Reference": [
        ("ARC: Frequencies", ARC_WIKI + "ARC_frequencies"),
        ("ARC: Repeaters @ UCF", ARC_WIKI + "ARCatUCF_repeater"),
        ("ARC: Band plan", ARC_WIKI + "Band_plan"),
    ],
}

EXAMS = {
    "tech": {"element": 2, "total": 35, "pass": "26/35 (74%)"},
    "general": {"element": 3, "total": 35, "pass": "26/35 (74%)"},
    "extra": {"element": 4, "total": 50, "pass": "37/50 (74%)"},
}


class Education(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Show ARC & ham-radio useful links")
    async def links(self, interaction: discord.Interaction):
        embed = discord.Embed(title="ARC Useful Links")
        for cat, items in LINKS.items():
            lines = [f"`{name}` – {url}" for name, url in items]
            embed.add_field(name=cat, value="\n".join(lines), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(description="Exam facts and optional study guide")
    @app_commands.describe(
        level="tech | general | extra", study_guide="include study links"
    )
    async def exam(
        self, interaction: discord.Interaction, level: str, study_guide: bool = False
    ):
        key = level.lower()
        if key not in EXAMS:
            return await interaction.response.send_message(
                "Levels: tech, general, extra", ephemeral=True
            )
        info = EXAMS[key]
        embed = discord.Embed(title=f"{level.title()} Exam")
        embed.add_field(name="Element", value=str(info["element"]))
        embed.add_field(name="Questions", value=str(info["total"]))
        embed.add_field(name="Passing", value=info["pass"])
        embed.add_field(name="Official FCC info", value=FCC_EXAMS, inline=False)
        if study_guide:
            if key == "tech":
                study = [("ARRL: Technician", ARRL_TECH)]
            else:
                study = []
            study += [
                ("ARRL: Question pools", ARRL_POOLS),
                ("ARC: Amateur radio testing", ARC_WIKI + "Amateur_radio_testing"),
            ]
            if key == "general":
                study.insert(
                    0,
                    (
                        "ARC: General study guide",
                        ARC_WIKI + "Amateur_Radio_General_Element_3_(2007)",
                    ),
                )
            embed.add_field(
                name="Study",
                value="\n".join(f"`{n}` – {u}" for n, u in study),
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=False)


async def setup(bot):
    await bot.add_cog(Education(bot))
