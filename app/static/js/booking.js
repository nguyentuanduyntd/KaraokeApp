// Hàm chuyển bước (1 -> 2 -> 3)
function goToStep(step) {
    // Ẩn tất cả các bước
    document.querySelectorAll('.step-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.step-indicator li').forEach(el => el.classList.remove('active'));

    // Hiện bước mong muốn
    document.getElementById('step-' + step).classList.add('active');

    // Cập nhật thanh stepper (active các bước trước đó nữa)
    for (let i = 1; i <= step; i++) {
        document.getElementById('indicator-' + i).classList.add('active');
    }

    // Nếu chuyển sang bước 3, cập nhật thông tin tóm tắt
    if (step === 3) {
        updateSummary();
    }
}
function calculatePrice() {
    const roomSelect = document.getElementById('room_select');
    const pricePerHour = parseFloat(roomSelect.options[roomSelect.selectedIndex].dataset.price);

    const dateInput = document.getElementById('booking_date').value;
    const startTime = document.getElementById('start_time').value;
    const endTime = document.getElementById('end_time').value;

    if (!dateInput || !startTime || !endTime) {
        document.getElementById('price-display').classList.add('d-none');
        return 0;
    }

    const start = new Date(`${dateInput}T${startTime}`);
    const end = new Date(`${dateInput}T${endTime}`);

    let diff = end - start;

    if (isNaN(diff) || diff <= 0) {
        document.getElementById('price-display').classList.add('d-none');
        return 0;
    }

    const hours = diff / 1000 / 60 / 60;
    const total = hours * pricePerHour;

    // ⭐ Làm tròn tiền VNĐ
    const totalRounded = Math.round(total);

    document.getElementById('total_amount_display').innerText =
        totalRounded.toLocaleString('vi-VN') + ' VNĐ';

    document.getElementById('duration_display').innerText =
        hours.toFixed(1);

    document.getElementById('price-display').classList.remove('d-none');

    return totalRounded;
}




// Kiểm tra hợp lệ bước 1
function validateStep1() {
    const date = document.getElementById('booking_date').value;
    const start = document.getElementById('start_time').value;
    const end = document.getElementById('end_time').value;
    const priceBox = document.getElementById('price-display');

    if (!date || !start || !end) {
        alert("Vui lòng chọn đầy đủ ngày và giờ!");
        return;
    }

    const startTime = new Date(`${date}T${start}`);
    const endTime = new Date(`${date}T${end}`);

    if (isNaN(startTime) || isNaN(endTime) || endTime <= startTime) {
        alert("Giờ đặt không hợp lệ (Giờ kết thúc phải sau giờ bắt đầu)!");
        return;
    }

    goToStep(2);
}


// Cập nhật thông tin tóm tắt ở bước 3
function updateSummary() {
    const roomSelect = document.getElementById('room_select');
    const roomName = roomSelect.options[roomSelect.selectedIndex].dataset.name;

    const date = document.getElementById('booking_date').value;
    const start = document.getElementById('start_time').value;
    const end = document.getElementById('end_time').value;
    const totalText = document.getElementById('total_amount_display').innerText;

    document.getElementById('confirm_room_name').innerText = roomName;
    document.getElementById('confirm_time').innerText = `${date} | ${start} - ${end}`;
    document.getElementById('confirm_total').innerText = totalText;

//    document.getElementById('confirm_room_id').value = document.getElementById('room_select').value;
//    document.getElementById('confirm_date').value = date;
//    document.getElementById('confirm_start').value = start;
//    document.getElementById('confirm_end').value = end;

}

// Gán sự kiện mặc định khi trang tải xong (Optional)
document.addEventListener('DOMContentLoaded', function() {
    // Có thể gọi calculatePrice() ngay lập tức nếu muốn tính tiền mặc định khi load
    // calculatePrice();
});