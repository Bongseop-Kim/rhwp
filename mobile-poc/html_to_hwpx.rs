//! S0-4 탐침: 빈 문서에 HTML 을 코어 `paste_html_native` 로 붙여 HWPX 로 내보낸다.
//! 네이티브 편집기(`native_host::clipboard`)는 표·개체 HTML 을 거부하므로 코어를 직접 부른다.
//! 사용: cargo run --release --example mobile_poc_html_to_hwpx -- in.html out.hwpx
use rhwp::DocumentCore;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let html = std::fs::read_to_string(&args[1]).expect("read html");
    let mut core = DocumentCore::new_empty();
    core.create_blank_document_native().expect("blank");
    let result = core.paste_html_native(0, 0, 0, &html).expect("paste");
    println!("paste: {result}");
    let bytes = core.export_hwpx_native().expect("export");
    std::fs::write(&args[2], &bytes).expect("write");
    println!("hwpx bytes: {}", bytes.len());
    // S0-5 탐침: 본문 전체를 코어의 HTML 내보내기로 뽑아 본다(호환 HTML 후보).
    let last = core.document().sections[0].paragraphs.len() - 1;
    let end = core.document().sections[0].paragraphs[last].text.chars().count();
    let html = core.export_selection_html_native(0, 0, 0, last, end).expect("html");
    std::fs::write(format!("{}.html", &args[2]), &html).expect("write html");
    println!("html bytes: {}", html.len());
}
