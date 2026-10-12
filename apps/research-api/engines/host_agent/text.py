def save_report(state: State) -> State:
    """最终报告 .md 落盘"""
    report = state.get("final_report")
    if not report:
        return {}
    output_dir = get_settings().HOST_REPORT_DIR
    md_path = save_md_report(output_dir, "Host", state['query'], report)
    logger.info(f"HostAgent: 最终报告已落盘 {md_path}")
    return {}
