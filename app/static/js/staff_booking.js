// =========================
// HÀM CHUYỂN STEP CHUNG
// =========================
function goToStep(step) {
    // Ẩn tất cả step
    document.querySelectorAll(".step-content").forEach(s => {
        s.classList.remove("active");
        s.classList.add("d-none");
    });

    // Kích hoạt step cần đến
    let activeStep = document.getElementById("step-" + step);
    activeStep.classList.remove("d-none");
    activeStep.classList.add("active");

    // Cập nhật step indicator
    document.querySelectorAll(".step-indicator li").forEach(i => i.classList.remove("active"));
    document.getElementById("indicator-" + step).classList.add("active");

    // Khi sang step 3 → cập nhật thông tin xác nhận
    if (step === 3) updateConfirmInfo();
}


// =========================
// STEP 1 → STEP 2
// =========================
function goToStep2() {
    let room = document.getElementById("room_select").value;
    let date = document.getElementById("booking_date").value;
    let start = document.getElementById("start_time").value;
    let end = document.getElementById("end_time").value;

    if (!room || !date || !start || !end) {
        alert("Vui lòng nhập đầy đủ thông tin!");
        return;
    }

    goToStep(2);
}


// =========================
// HIỆN THỊ XÁC NHẬN Ở STEP 3
// =========================
function updateConfirmInfo() {
    // Thông tin khách
    document.getElementById("confirm_guest_name").innerText =
        document.getElementById("guest_name").value;

    document.getElementById("confirm_guest_phone").innerText =
        document.getElementById("guest_phone").value;

    // Thông tin phòng
    let roomSelect = document.getElementById("room_select");
    let roomName = roomSelect.options[roomSelect.selectedIndex].dataset.name;
    document.getElementById("confirm_room_name").innerText = roomName;

    // Thời gian
    let date = document.getElementById("booking_date").value;
    let start = document.getElementById("start_time").value;
    let end = document.getElementById("end_time").value;

    document.getElementById("confirm_time").innerText =
        `${date} | ${start} → ${end}`;

    // Tổng tiền
    document.getElementById("confirm_total").innerText =
        document.getElementById("total_amount_display").innerText;
}


// =========================
// TÍNH GIÁ TIỀN
// =========================
function calculatePrice() {
    let roomSelect = document.getElementById("room_select");
    let price = roomSelect.options[roomSelect.selectedIndex].dataset.price;

    let start = document.getElementById("start_time").value;
    let end = document.getElementById("end_time").value;

    if (!start || !end) return;

    let startTime = new Date("2000-01-01 " + start);
    let endTime = new Date("2000-01-01 " + end);

    if (endTime <= startTime) {
        document.getElementById("total_amount_display").innerText = "0 VNĐ";
        document.getElementById("duration_display").innerText = "0";
        return;
    }

    let duration = (endTime - startTime) / (1000 * 60 * 60);
    let total = duration * price;

    document.getElementById("price-display").classList.remove("d-none");

    document.getElementById("duration_display").innerText =
        duration.toFixed(1);

    document.getElementById("total_amount_display").innerText =
        Number(total).toLocaleString("vi-VN") + " VNĐ";
}
