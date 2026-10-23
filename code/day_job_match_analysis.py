from pathlib import Path
from math import ceil

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from common import OUTPUT_DIR


PROJECT_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = Path.home() / "Downloads"
UNLIMITED_FILE = (
    DOWNLOAD_DIR
    / "湖南科技大学2026年秋季毕业生供需见面会参会单位岗位信息-不限专业.xlsx"
)
COMPUTER_FILE = (
    DOWNLOAD_DIR
    / "湖南科技大学2026年秋季毕业生供需见面会参会单位岗位信息-计算机相关专业.xlsx"
)


PROFILE = {
    "strong": (
        "Python/pandas/NumPy、SQL/DuckDB、Excel看板、指标体系、DAU/留存/cohort、"
        "用户与内容分层、异常监控、基础统计、A/B方案、scikit-learn基础模型"
    ),
    "basic": "PyTorch MLP、PySpark DataFrame/Join/窗口/Shuffle概念、R复现图",
    "missing": (
        "C/C++/Java/.NET开发、前端/后端、嵌入式/FPGA/PLC/LabVIEW、硬件、"
        "生产级算法/大模型、Linux/网络运维、真实推荐曝光日志和正式A/B实验"
    ),
}


DIRECT = [
    {
        "company": "湖南向上商旅服务有限公司",
        "role": "数据分析员",
        "level": "A-优先投递",
        "reason": "岗位名称与项目中的SQL、Python、Excel、指标分析和报告能力直接对应。",
        "gap": "补充业务数据口径、Excel函数和面试中的案例表达。",
        "source": "不限专业表",
    },
    {
        "company": "意拉德电子（东莞）有限公司",
        "role": "大数据及人工智能应用实习生",
        "level": "A-优先投递",
        "reason": "已有Python、基础机器学习、PyTorch、PySpark和AI应用项目，可作为实习/助理级岗位切入。",
        "gap": "岗位为实习生，确认毕业身份和实习时间；补充数据清洗、接口和简单部署。",
        "source": "不限专业表",
    },
    {
        "company": "意拉德电子（东莞）有限公司",
        "role": "应用系统需求分析及方案实施实习生",
        "level": "A-优先投递",
        "reason": "业务问题拆解、指标定义、报告和看板经验可迁移到需求分析与实施支持。",
        "gap": "补ERP/OA/企业系统基础、需求文档和流程图。",
        "source": "不限专业表",
    },
    {
        "company": "中国人民财产保险股份有限公司湘潭市分公司",
        "role": "车险数据分析岗",
        "level": "A-/B+",
        "reason": "数据分析项目、统计检验、指标监控和异常排查能力高度相关。",
        "gap": "补保险业务、理赔指标和SQL面试；确认该岗位的专业及学历限制。",
        "source": "不限专业表",
    },
    {
        "company": "中国平安财产保险股份有限公司湖北分公司",
        "role": "27届湖北分公司数据管培生",
        "level": "A-/B+",
        "reason": "管培/数据方向与项目中的经营分析、指标体系和跨工具输出匹配。",
        "gap": "确认是否只招27届、工作地点和是否需要金融/统计背景。",
        "source": "不限专业表",
    },
    {
        "company": "杭州卡日曲网络科技有限公司",
        "role": "游戏增长策略管培生；游戏运营管培生",
        "level": "A-/B+",
        "reason": "内容平台增长、用户分层、留存、推荐策略和A/B实验项目可迁移到游戏增长/运营。",
        "gap": "补游戏指标：付费、次留、活跃、关卡漏斗和活动分析；确认毕业届次。",
        "source": "计算机相关专业表",
    },
]


CONDITIONAL = [
    {
        "company": "湖南长银五八消费金融股份有限公司",
        "role": "全面风险管理岗",
        "level": "B-可投，需补业务",
        "reason": "统计、异常监控、用户分层和模型基础可迁移到风险分析。",
        "gap": "缺金融风控、评分卡、授信/逾期指标和监管知识。",
        "source": "计算机相关专业表",
    },
    {
        "company": "长沙迪迈科技股份有限公司",
        "role": "AI产品经理；解决方案工程师；咨询规划师",
        "level": "B-可投，偏产品/方案",
        "reason": "已经做过业务问题、指标、实验设计和项目报告，适合助理级产品/方案沟通。",
        "gap": "缺矿业领域、需求文档、客户访谈和售前交付经验。",
        "source": "计算机相关专业表",
    },
    {
        "company": "拓维信息系统股份有限公司",
        "role": "AI产品经理；AI解决方案；PVZ2游戏产品运营",
        "level": "B-可投其中产品/运营岗",
        "reason": "项目包含推荐分析、用户留存、看板和A/B方案，产品运营方向有可展示证据。",
        "gap": "AI产品/解决方案需要真实产品流程、客户交付和LLM应用经验；岗位标注27届需核对。",
        "source": "计算机相关专业表",
    },
    {
        "company": "深圳出海一叮科技有限公司长沙分公司",
        "role": "SaaS产品经理；海外市场运营；海外广告投放",
        "level": "B-可投产品/运营岗",
        "reason": "指标、用户分群、实验和内容平台分析能支撑产品运营分析。",
        "gap": "缺SaaS产品、广告投放、跨境平台和英文业务经验。",
        "source": "计算机相关专业表",
    },
    {
        "company": "广州英码信息科技有限公司",
        "role": "产品助理；交付支持工程师；软件交付工程师",
        "level": "B-可投助理/支持岗",
        "reason": "业务分析、报告、SQL指标和项目复盘能力可用于需求整理、交付文档和客户支持。",
        "gap": "缺企业软件交付、接口调试、部署和客户现场经验。",
        "source": "计算机相关专业表",
    },
    {
        "company": "湖南硅谷融创科技有限公司",
        "role": "实施运维工程师",
        "level": "B-可投，需补运维",
        "reason": "Python/SQL和问题排查方法可用于实施数据核对和报表支持。",
        "gap": "缺Linux、网络、数据库运维、部署和故障处理。",
        "source": "不限专业表",
    },
    {
        "company": "湖南亚太实业有限公司",
        "role": "信息化助理工程师",
        "level": "B-可投助理岗",
        "reason": "数据表、指标、Excel和业务流程分析有迁移价值。",
        "gap": "缺ERP/OA、权限、网络和企业信息化实施经验。",
        "source": "计算机相关专业表",
    },
    {
        "company": "浙江永太科技股份有限公司",
        "role": "IT专员；IT与自控技术员",
        "level": "B-可投IT专员",
        "reason": "计算机基础、数据处理和问题排查可支持初级IT/应用岗位。",
        "gap": "缺桌面运维、网络、硬件和自控系统经验；IT与自控技术员不建议作为首选。",
        "source": "计算机相关专业表",
    },
    {
        "company": "乔锋智能装备股份有限公司",
        "role": "IT助理；运营管培生",
        "level": "B-可投",
        "reason": "IT助理与数据/系统支持有一定匹配，运营管培生可使用指标和Excel能力。",
        "gap": "岗位职责不清，需现场确认IT是应用支持还是网络/硬件；运营岗可能偏制造业务。",
        "source": "计算机相关专业表",
    },
    {
        "company": "巴德富集团有限公司",
        "role": "IT应用助理工程师；AI应用助理工程师",
        "level": "B-可投助理级",
        "reason": "项目中的AI应用、Python、SQL、看板和业务分析适合助理级应用岗位。",
        "gap": "补企业应用、接口、权限、部署；AI应用岗位需确认是否要求模型开发。",
        "source": "计算机相关专业表",
    },
    {
        "company": "浙江省公众信息产业有限公司",
        "role": "AI运营工程师；互联网产品运营",
        "level": "B-可投运营岗",
        "reason": "内容平台增长、用户分层、留存和实验设计与运营分析相关。",
        "gap": "缺AI运营流程、知识库/提示词、客户运营和大数据平台经验。",
        "source": "计算机相关专业表",
    },
    {
        "company": "杭州铭师堂数字科技有限公司",
        "role": "互联网类产品专员/研发工程师方向",
        "level": "B-可投产品专员",
        "reason": "业务分析、看板和实验方案适合产品专员或运营分析，不足以支撑研发工程师。",
        "gap": "确认岗位组内具体方向；研发工程师需要开发语言和工程项目。",
        "source": "计算机相关专业表",
    },
    {
        "company": "广东德晟智能科技有限公司",
        "role": "技术支持工程师；测试工程师；项目工程师",
        "level": "B-可投支持/项目岗",
        "reason": "SQL、问题拆解、质量检查、报告和项目管理基础可迁移。",
        "gap": "测试工程师若要求自动化测试不匹配；技术支持需补设备/制造领域知识。",
        "source": "计算机相关专业表",
    },
    {
        "company": "中科开创（广州）智能科技发展有限公司",
        "role": "技术支持工程师；技术营销工程师",
        "level": "B-可投支持/方案岗",
        "reason": "分析报告、指标解释和项目讲解能力可用于解决方案支持。",
        "gap": "缺硬件/设备/行业解决方案知识和售前沟通经历。",
        "source": "计算机相关专业表",
    },
    {
        "company": "杰创智能科技股份有限公司",
        "role": "技术支持工程师；销售运营支持",
        "level": "B-可投支持岗",
        "reason": "业务分析、看板、数据解释和跨团队沟通有迁移价值。",
        "gap": "数据中心运维、机器人算法、前后端和嵌入式岗位不匹配。",
        "source": "计算机相关专业表",
    },
]


NOT_YET = [
    {
        "category": "开发工程师",
        "roles": "前端、后端、Java、C/C++、C#/.NET、鸿蒙应用、软件开发",
        "reason": "本月没有系统学习对应语言、框架、数据结构、工程开发和部署，不能把Python分析项目当成开发经验。",
    },
    {
        "category": "嵌入式/硬件/自动化",
        "roles": "嵌入式、FPGA、PLC、驱动、上位机、LabVIEW、硬件、电子、电气、机器人应用",
        "reason": "岗位核心是硬件、控制、实时系统或设备调试，与SQL/Python业务分析主线不同。",
    },
    {
        "category": "算法/AI研发",
        "roles": "AI算法、传统算法、SLAM、视觉、导航、通信算法、AI研发、AI大模型工程师",
        "reason": "只有基础模型和PyTorch MLP，没有生产级算法、深度学习体系、计算机视觉/SLAM、LLM微调或论文/竞赛证据。",
    },
    {
        "category": "数据工程/大数据开发",
        "roles": "大数据开发、AI数据工程师、数据开发、Spark工程师",
        "reason": "PySpark只完成本地可复现抽样和指标计算，没有数据仓库、ETL、调度、集群资源和生产数据管道经验。",
    },
    {
        "category": "系统/网络运维",
        "roles": "数据中心运维、系统运维、Linux全栈、组网、信息安全工程师",
        "reason": "没有Linux、网络、安全、监控、部署和故障响应的实操证据。IT应用助理可以投，但不能等同于系统运维。",
    },
]


ENTRY_COMPUTER = [
    {
        "category": "数据分析/经营分析",
        "roles": "数据分析员、数据管培生、车险数据分析岗、经营/风险分析助理",
        "assessment": "可作为主投方向",
        "reason": "已有SQL、Python/pandas、Excel看板、指标体系、留存/分层/异常监控和基础模型项目。入职后仍需熟悉业务，但岗位核心工作与现有项目直接相关。",
    },
    {
        "category": "AI/数据应用助理",
        "roles": "大数据及人工智能应用实习生、AI应用助理工程师、AI运营工程师",
        "assessment": "可以投助理/实习级",
        "reason": "已有Python、基础机器学习、PyTorch、PySpark和AI概念，但还不能承诺生产级算法或大模型开发。",
    },
    {
        "category": "产品/增长/运营分析",
        "roles": "游戏增长策略、游戏运营、互联网产品运营、产品助理、AI产品助理",
        "assessment": "可以投初级岗位",
        "reason": "已有用户增长、内容表现、留存、推荐策略、A/B实验和Dashboard项目；需要补具体行业和产品流程。",
    },
    {
        "category": "实施/技术支持/IT应用",
        "roles": "应用系统需求分析、方案实施、交付支持、技术支持、IT应用助理、信息化助理",
        "assessment": "可以投但需培训",
        "reason": "SQL、数据核对、问题拆解、报告和项目沟通可迁移；需要补ERP/OA、API、Linux、网络和部署。",
    },
    {
        "category": "测试/质量助理",
        "roles": "软件测试管培生、测试助理、质量数据助理",
        "assessment": "可作为次要方向",
        "reason": "数据质量检查、异常排查和结构化分析能力有帮助；但需要补测试用例、缺陷管理、接口测试和自动化测试。",
    },
]


def load_sources():
    frames = []
    for source, path in [
        ("不限专业表", UNLIMITED_FILE),
        ("计算机相关专业表", COMPUTER_FILE),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"岗位文件不存在: {path}")
        frame = pd.read_excel(path)
        frame["source"] = source
        frame["excel_row"] = frame.index + 2
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def attach_source_details(items, source_frame):
    rows = []
    for item in items:
        matches = source_frame[
            source_frame["单位名称"].astype(str).str.strip()
            == item["company"]
        ]
        if matches.empty:
            rows.append({**item, "source_row": "not found"})
            continue
        for _, match in matches.drop_duplicates(
            subset=["单位名称", "source"]
        ).iterrows():
            rows.append(
                {
                    **item,
                    "source_row": int(match["excel_row"]),
                    "industry": match["所属行业"],
                    "province": match["所在省份"],
                    "city": match["所在城市"],
                    "listed_positions": match["招聘岗位"],
                    "listed_major": match["需求专业"],
                    "headcount": match["需求人数"],
                }
            )
    return pd.DataFrame(rows)


def format_match_sheet(worksheet, widths):
    """Make long job descriptions readable in Excel without truncation."""
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.sheet_view.showGridLines = False
    worksheet.sheet_properties.pageSetUpPr.fitToPage = True
    worksheet.page_setup.orientation = "landscape"
    worksheet.page_setup.fitToWidth = 1
    worksheet.page_setup.fitToHeight = 0

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(bold=True, color="FFFFFF")
    thin_border = Border(
        bottom=Side(style="thin", color="D9E2F3")
    )

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )
        cell.border = thin_border
    worksheet.row_dimensions[1].height = 32

    for column_index, cell in enumerate(worksheet[1], start=1):
        header = str(cell.value)
        width = widths.get(header)
        if width is None:
            values = [
                len(str(row[column_index - 1].value))
                for row in worksheet.iter_rows(min_row=2)
                if row[column_index - 1].value is not None
            ]
            width = min(max(max(values, default=10) + 2, 12), 36)
        worksheet.column_dimensions[cell.column_letter].width = width

    for row in worksheet.iter_rows(min_row=2):
        max_lines = 1
        for cell in row:
            value = "" if cell.value is None else str(cell.value)
            width = worksheet.column_dimensions[cell.column_letter].width or 12
            estimated_lines = max(1, ceil(len(value) / max(width - 2, 1)))
            max_lines = max(max_lines, estimated_lines)
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )
            cell.border = thin_border
        worksheet.row_dimensions[row[0].row].height = min(
            max(22, max_lines * 18),
            150,
        )

def format_match_workbook(path):
    workbook = load_workbook(path)
    sheet_widths = {
        "profile": {"section": 18, "skills": 82},
        "criteria": {"level": 22, "meaning": 76},
        "A_direct": {
            "company": 28,
            "role": 42,
            "level": 18,
            "reason": 54,
            "gap": 54,
            "source": 18,
            "source_row": 12,
            "industry": 24,
            "province": 18,
            "city": 16,
            "listed_positions": 64,
            "listed_major": 82,
            "headcount": 12,
        },
        "B_conditional": {
            "company": 28,
            "role": 42,
            "level": 22,
            "reason": 54,
            "gap": 54,
            "source": 18,
            "source_row": 12,
            "industry": 24,
            "province": 18,
            "city": 16,
            "listed_positions": 64,
            "listed_major": 82,
            "headcount": 12,
        },
        "B_computer_entry": {
            "category": 26,
            "roles": 66,
            "assessment": 24,
            "reason": 90,
        },
        "C_core_engineering_gap": {
            "category": 26,
            "roles": 66,
            "reason": 88,
        },
    }
    for worksheet in workbook.worksheets:
        format_match_sheet(
            worksheet,
            sheet_widths.get(worksheet.title, {}),
        )
    workbook.save(path)


def main() -> None:
    source_frame = load_sources()
    direct = attach_source_details(DIRECT, source_frame)
    conditional = attach_source_details(CONDITIONAL, source_frame)
    computer_entry = pd.DataFrame(ENTRY_COMPUTER)
    not_yet = pd.DataFrame(NOT_YET)

    profile = pd.DataFrame(
        [
            {"section": "可独立展示", "skills": PROFILE["strong"]},
            {"section": "基础接触", "skills": PROFILE["basic"]},
            {"section": "当前缺口", "skills": PROFILE["missing"]},
        ]
    )
    criteria = pd.DataFrame(
        [
            {
                "level": "A-优先投递",
                "meaning": "岗位核心工作与现有项目直接对应，可作为主投，但仍需满足专业/届次/地点要求。",
            },
            {
                "level": "B-可投，需补强",
                "meaning": "基础能力可迁移，但岗位有明显业务或工程缺口，适合投递并在面试前补齐。",
            },
            {
                "level": "C-暂不匹配",
                "meaning": "核心工程技能不是本月主线，当前不能诚实地写成可独立承担；不代表不能做任何计算机相关工作。",
            },
        ]
    )

    output = OUTPUT_DIR / "ml_job_match_analysis.xlsx"
    try:
        writer = pd.ExcelWriter(output, engine="openpyxl")
    except PermissionError:
        output = OUTPUT_DIR / "ml_job_match_analysis_updated.xlsx"
        writer = pd.ExcelWriter(output, engine="openpyxl")
        print(
            "The original workbook is open or locked; writing an updated copy."
        )
    with writer:
        profile.to_excel(writer, sheet_name="profile", index=False)
        criteria.to_excel(writer, sheet_name="criteria", index=False)
        direct.to_excel(writer, sheet_name="A_direct", index=False)
        conditional.to_excel(writer, sheet_name="B_conditional", index=False)
        computer_entry.to_excel(
            writer,
            sheet_name="B_computer_entry",
            index=False,
        )
        not_yet.to_excel(
            writer,
            sheet_name="C_core_engineering_gap",
            index=False,
        )
    format_match_workbook(output)

    direct.to_csv(
        OUTPUT_DIR / "ml_job_match_A_direct.csv",
        index=False,
        encoding="utf-8-sig",
    )
    conditional.to_csv(
        OUTPUT_DIR / "ml_job_match_B_conditional.csv",
        index=False,
        encoding="utf-8-sig",
    )

    report = """# 岗位匹配分析

## 结论

你不是“无法胜任任何计算机工作”。更准确的判断是：你目前可以胜任或争取数据分析、经营/风险分析、内容/游戏增长运营、产品/方案助理、AI/数据应用助理、实施支持和IT应用助理等初级方向；但还不能把自己包装成可以独立承担开发、嵌入式、算法、硬件、系统运维和生产级大数据岗位核心工作的候选人。

## 重要假设

本报告只根据本月学习和项目成果判断，不包含你的学历、专业、英语、实习经历、毕业届次、地点意愿和薪资要求。所有岗位还要单独核对这些硬条件。

岗位表一行可能把多个岗位合并展示，下面的推荐只针对“建议投递的岗位名称”，不是该公司这一整行的所有岗位。

## A档：优先投递

主要证据：

- `湖南向上商旅服务有限公司-数据分析员`：与SQL、Python、Excel、指标分析直接匹配。
- `意拉德电子-大数据及人工智能应用实习生`：适合以助理/实习级别切入，但要确认实习和毕业要求。
- `意拉德电子-应用系统需求分析及方案实施实习生`：业务问题拆解、指标定义、报告和看板可以迁移。
- `中国人保湘潭-车险数据分析岗`：可投，但要补保险业务和风险指标。
- `中国平安湖北-数据管培生`：可投，但必须确认27届、地点和专业条件。
- `杭州卡日曲-游戏增长策略管培生/游戏运营管培生`：与增长、留存、内容推荐和A/B实验匹配，需确认届次。

## B档：可以投，但不要作为唯一主线

- AI产品经理、AI产品助理、AI解决方案、互联网产品运营。
- 应用系统实施、交付支持、技术支持、销售运营支持。
- IT应用助理、信息化助理、IT专员、IT助理。
- 消费金融风险管理、制造业运营/项目助理。

这些岗位的共同缺口是企业系统、行业业务、客户交付、Linux/网络、需求文档或具体产品经验。简历可以写已完成的分析项目，但不能写成有生产系统经验。

## B档新增：可以做的计算机相关初级工作

- 数据分析、经营分析、风险分析助理：这是当前最匹配的数据/计算机方向。
- AI/数据应用助理：可以做数据处理、指标、应用验证和简单模型，不等于算法工程师。
- 产品/增长/运营分析：可以做指标、用户分层、内容分析和实验支持。
- 实施、技术支持、IT应用助理：可以做数据核对、报表、需求整理和一线支持，但要补企业系统和部署知识。
- 测试/质量助理：可以投培训生或助理级岗位，但还需要补测试用例、接口测试和自动化测试。

## C档：核心工程能力尚未形成

- 前端、后端、Java、C/C++、C#/.NET、鸿蒙开发。
- 嵌入式、FPGA、PLC、驱动、上位机、硬件和机器人应用。
- AI算法、SLAM、视觉、传统算法、AI研发、AI大模型工程师。
- 大数据开发、数据工程、AI数据工程师。
- 数据中心运维、Linux/网络/组网、信息安全工程师。

这不是“不能做任何计算机工作”，而是说明你目前不能把自己包装成可以独立承担这些岗位核心工作的候选人。即使岗位写“不限专业”，也不等于一个月的SQL/Python分析项目能够替代开发或算法项目。

## 投递顺序

1. 数据分析员、数据管培生、车险数据分析岗、风险管理岗。
2. 游戏增长策略、游戏运营、内容/产品运营。
3. AI应用助理、应用系统需求分析与实施、产品助理、解决方案/技术支持。
4. IT应用助理、信息化助理、测试/质量助理作为保底方向。

## 面试时的真实表述

可以说：

> 我用公开 MovieLens 数据完成了 SQL 指标体系、Python 清洗与建模、Excel 看板、A/B方案和基础 PyTorch/PySpark 项目。

不要说：

> 我精通大模型、推荐算法、Java/C++开发或生产级大数据平台。

## 下一步补强

- 数据岗：准备 4 道限时 SQL，并补行业指标案例。
- 产品/运营岗：把项目发现改写成用户问题、行动、验证三段式。
- IT/实施岗：补 SQL Server/MySQL、Linux、HTTP/API、ERP/OA和需求文档。
- AI岗：补一个真实可运行的文本分类或推荐模型，明确训练/验证/部署边界。
"""
    (OUTPUT_DIR / "ml_job_match_analysis.md").write_text(
        report,
        encoding="utf-8",
    )
    print(f"Saved: {output}")
    print(f"A direct roles: {len(direct)}")
    print(f"B conditional roles: {len(conditional)}")


if __name__ == "__main__":
    main()
