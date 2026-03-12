document.addEventListener("DOMContentLoaded", () => {
  const currentUser = "{{ username }}";
  const storageKey = `theme_${currentUser}`;
  let toggled = localStorage.getItem(storageKey) === "alt";

  const bgLayer = document.getElementById("bg-layer");
  const root = document.documentElement;
  const header = document.querySelector("header");
  const colorBtn = document.getElementById("color");

  function applyTheme() {
    bgLayer.style.backgroundImage = toggled
      ? "url('/static/imgs/banner2.jpg')"
      : "url('/static/imgs/banner.jpg')";

    if (toggled) {
      root.style.setProperty('--main-font', '#000000');
      root.style.setProperty('--sec-col', '#ffffff4e');      
      root.style.setProperty('--highlight-blue', '#0d284eff');
      root.style.setProperty('--sec2-col', '#81baff');
      root.style.setProperty('--black-white', '#ffffff')

      header && (header.style.background = 
        "linear-gradient(90deg, #6aa1e077, #00f7ff00, #6aa1e077)"
      );
    } else {
      root.style.setProperty('--main-font', '#ffffff');
      root.style.setProperty('--highlight-blue', '#76c3ff');
      root.style.setProperty('--sec-col', '#141c25c5');
      root.style.setProperty('--sec2-col', '#17202b');
      root.style.setProperty('--black-white', '#000000ff')

      header && (header.style.background = 
        "linear-gradient(90deg, #162137a2, #00f7ff00, #162137a2)"
      );
    }
  }

  // Apply saved theme immediately
  applyTheme();

  const video = document.getElementById('bgvid');
  colorBtn?.addEventListener('click', () => {
    toggled = !toggled;
    localStorage.setItem(storageKey, toggled ? 'alt' : 'default');
    video?.classList.toggle('dimmed');
    bgLayer.style.opacity = 0;
    if (video) {
      video.style.filter = toggled ? 'brightness(1)' : 'brightness(0.5)';
    }
    setTimeout(() => {
      applyTheme();
      bgLayer.style.opacity = 1;
    }, 500);
  });


  document.querySelectorAll('.auction-card').forEach(card => {
    if (card.dataset.status === 'closed') {
      card.querySelector('.expand-btn')?.remove();
      card.querySelector('.bid-form')?.remove();
      const disc = card.querySelector('.auction-disc');
      const winner = card.dataset.winner || 'None';
      disc.insertAdjacentHTML('beforeend',
        `<p class="auction-ended">Auction ended. Winner: ${winner}</p>`
      );
    }
  });

  // Nav Highlight Movement
  const highlight = document.getElementById('highlight');
  const links = document.querySelectorAll('.nav-link');

  function moveHighlight(link) {
    const rect = link.getBoundingClientRect();
    const nav = link.parentElement.getBoundingClientRect();
    highlight.style.width = `${rect.width}px`;
    highlight.style.left = `${rect.left - nav.left}px`;
  }

  const homeLink = document.querySelector('.nav-link[href="#home"]');
  if (homeLink && highlight) moveHighlight(homeLink);

  links.forEach(link => {
    link.addEventListener('click', () => moveHighlight(link));
  });

  // Expand Auction Cards
  document.querySelectorAll('.expand-btn').forEach(button => {
    button.addEventListener('click', () => {
      const card = button.closest('.auction-card');
      if (card) {
        card.classList.toggle('expanded');
        // button.textContent = 'Expand'; // Optional: can remove this if unnecessary
      }
    });
  });

  // Role-based Redirect
  const userProfileBtn = document.getElementById("user-profile");
  if (userProfileBtn) {
    const role = userProfileBtn.dataset.role;
    userProfileBtn.addEventListener("click", () => {
      if (role === "auctioneer") window.location.href = "/auctioneer";
      else if (role === "bidder") window.location.href = "/bidder";
    });
  }

  // Password Toggle
  document.querySelectorAll('.password-toggle-icon').forEach(toggle => {
    toggle.addEventListener('click', () => {
      const input = toggle.previousElementSibling;
      const icon = toggle.querySelector('i');

      if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
      } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
      }
    });
  });

  // Logout
  const logoutBtn = document.getElementById("logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      fetch("/logout", { method: "POST" })
      .then(res => {
        if (res.ok) window.location.href = "/login";
        else alert("Logout failed");
      })
      .catch(err => console.error("Logout error:", err));
    });
  }

  // Initial Amount Input Validation
  const initialAmountInput = document.getElementById("initial_amount");
  if (initialAmountInput) {
    initialAmountInput.addEventListener("keydown", (e) => {
      if (e.key === "-" || e.key === "e") e.preventDefault();
    });

    initialAmountInput.addEventListener("input", () => {
      if (initialAmountInput.value < 1) initialAmountInput.value = "";
    });

    initialAmountInput.addEventListener("wheel", (e) => {
      const parent = initialAmountInput.closest(".currency-input");
      if (parent && parent.matches(":hover")) {
        e.preventDefault();
      }
    });
  }
});

 
function previewImage(event) {
  const file = event.target.files[0];
  const previewContainer = document.getElementById('preview-container');
  const previewImage = document.getElementById('imagePreview');
  const fileNameSpan = document.getElementById('fileName');

  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      previewImage.src = e.target.result;
      previewContainer.style.display = 'block';
      fileNameSpan.textContent = file.name;
    };
    reader.readAsDataURL(file);
  }
}

function removePreview() {
  document.getElementById('imagePreview').src = '#';
  document.getElementById('preview-container').style.display = 'none';
  document.getElementById('image-input').value = '';
  document.getElementById('fileName').textContent = 'No file chosen';
}

  document.getElementById("owl-mover").onclick = function () {
  const space2 = document.getElementById("owl-mover");
  const space3 = document.getElementById("eyes");
  const space4 = document.getElementById("user-nav");

  if (space2.style.left === "200px") {
    space2.style.left = "-40px";
    space3.style.left = "15px";
    space4.style.transform = "translateX(-250px)"
  } else {
    space2.style.left = "200px";
    space3.style.left = "255px";
    space4.style.transform = "translateX(0px)"
  }
};

setInterval(updateCountdowns, 1000); // updates every second