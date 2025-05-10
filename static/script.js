function addPhoneField() {
  const container = document.getElementById('phone-container');

  const wrapper = document.createElement('div');
  wrapper.className = 'd-flex align-items-center mb-2';

  const input = document.createElement('input');
  input.type = 'text';
  input.name = 'phone_numbers[]';
  input.className = 'form-control me-2';
  input.required = true;

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-outline-danger remove-phone';
  removeBtn.textContent = '×';
  removeBtn.onclick = () => {
    const allFields = container.querySelectorAll('input[name="phone_numbers[]"]');
    if (allFields.length > 1) {
      wrapper.remove();
    } else {
      alert("At least one phone number is required.");
    }
  };

  wrapper.appendChild(input);
  wrapper.appendChild(removeBtn);

  container.appendChild(wrapper);
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.remove-phone').forEach(btn => {
    btn.addEventListener('click', () => {
      const container = document.getElementById('phone-container');
      const allFields = container.querySelectorAll('input[name="phone_numbers[]"]');
      if (allFields.length > 1) {
        btn.parentElement.remove();
      } else {
        alert("At least one phone number is required.");
      }
    });
  });
});





  let cropper;
  const imageInput = document.getElementById('profile_image');
  const cropperImage = document.getElementById('cropper-image');
  const preview = document.getElementById('preview');
  const cropModal = new bootstrap.Modal(document.getElementById('cropModal'), { keyboard: false });

  imageInput.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      cropperImage.src = url;
      setTimeout(() => {
        cropper = new Cropper(cropperImage, {
          aspectRatio: 1,
          viewMode: 1,
          movable: true,
          zoomable: true,
          cropBoxResizable: true,
        });
        cropModal.show();
      }, 300);
    }
  });

  document.getElementById('crop-button').addEventListener('click', function () {
    const canvas = cropper.getCroppedCanvas({ width: 600, height: 600 });
    preview.src = canvas.toDataURL();
    preview.style.display = 'block';

    canvas.toBlob(blob => {
      const file = new File([blob], 'cropped.png', { type: 'image/png' });
      const container = new DataTransfer();
      container.items.add(file);
      imageInput.files = container.files;
    });

    cropModal.hide();
    cropper.destroy();
  });

  // فقط اجازه تایپ حروف انگلیسی
  function allowOnlyEnglishInput(selector) {
    document.querySelectorAll(selector).forEach(input => {
      input.addEventListener('keypress', function (e) {
        const char = String.fromCharCode(e.which);
        if (!/^[A-Za-z\s]+$/.test(char)) {
          e.preventDefault();
        }
      });

      input.addEventListener('input', function () {
        this.value = this.value.replace(/[^A-Za-z\s]/g, '');
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    allowOnlyEnglishInput('input[name="first_name"], input[name="last_name"]');
  });





  document.addEventListener("DOMContentLoaded", function () {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("DatePickerHidden").value = today;
  });


  $(document).ready(function () {
    $("#DatePickerDisplay").persianDatepicker({
      format: 'YYYY/MM/DD',
      autoClose: true,
      onSelect: function (unix) {
        var gregorianDate = moment(unix).format('YYYY-MM-DD');
        $("#DatePickerHidden").val(gregorianDate);
      }
    });
  });
