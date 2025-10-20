
        const jobDescriptions = {
            backend: {
                title: "Senior Backend Developer",
                content: `
                    <h3>Mô tả công việc:</h3>
                    <ul>
                        <li>Thiết kế và phát triển các API RESTful/GraphQL</li>
                        <li>Tối ưu hiệu suất hệ thống và database</li>
                        <li>Xây dựng kiến trúc microservices</li>
                        <li>Code review và mentor các thành viên junior</li>
                    </ul>
                    <h3>Yêu cầu:</h3>
                    <ul>
                        <li>5+ năm kinh nghiệm Backend Development</li>
                        <li>Thành thạo Node.js, Python hoặc Java</li>
                        <li>Kinh nghiệm với PostgreSQL, MongoDB, Redis</li>
                        <li>Hiểu biết về Docker, Kubernetes</li>
                    </ul>
                    <h3>Quyền lợi:</h3>
                    <ul>
                        <li>Lương cạnh tranh, thưởng theo hiệu suất</li>
                        <li>Bảo hiểm đầy đủ, khám sức khỏe định kỳ</li>
                        <li>Môi trường làm việc hiện đại, chuyên nghiệp</li>
                        <li>Cơ hội thăng tiến rõ ràng</li>
                    </ul>
                `
            },
            designer: {
                title: "UI/UX Designer",
                content: `
                    <h3>Mô tả công việc:</h3>
                    <ul>
                        <li>Thiết kế giao diện website và mobile app</li>
                        <li>Nghiên cứu user experience và user behavior</li>
                        <li>Tạo wireframe, prototype và mockup</li>
                        <li>Làm việc chặt chẽ với team development</li>
                    </ul>
                    <h3>Yêu cầu:</h3>
                    <ul>
                        <li>3+ năm kinh nghiệm UI/UX Design</li>
                        <li>Thành thạo Figma, Adobe XD, Sketch</li>
                        <li>Hiểu biết về Design System và Material Design</li>
                        <li>Portfolio ấn tượng</li>
                    </ul>
                    <h3>Quyền lợi:</h3>
                    <ul>
                        <li>Lương thỏa thuận theo năng lực</li>
                        <li>Làm việc với các dự án quốc tế</li>
                        <li>Đào tạo và phát triển kỹ năng liên tục</li>
                        <li>Team building, du lịch hàng năm</li>
                    </ul>
                `
            },
            mobile: {
                title: "Mobile Developer (React Native)",
                content: `
                    <h3>Mô tả công việc:</h3>
                    <ul>
                        <li>Phát triển ứng dụng mobile đa nền tảng với React Native</li>
                        <li>Tích hợp API và third-party services</li>
                        <li>Tối ưu hiệu suất ứng dụng</li>
                        <li>Fix bug và maintain code</li>
                    </ul>
                    <h3>Yêu cầu:</h3>
                    <ul>
                        <li>2+ năm kinh nghiệm React Native</li>
                        <li>Thành thạo JavaScript/TypeScript</li>
                        <li>Kinh nghiệm với Redux, Context API</li>
                        <li>Hiểu biết về iOS và Android native</li>
                    </ul>
                    <h3>Quyền lợi:</h3>
                    <ul>
                        <li>Mức lương hấp dẫn</li>
                        <li>Làm việc remote linh hoạt</li>
                        <li>Trang thiết bị làm việc hiện đại</li>
                        <li>Phụ cấp ăn trưa, xăng xe</li>
                    </ul>
                `
            }
        };

        let applicationData = {};

        function showApplicationForm() {
            document.getElementById('landingPage').style.display = 'none';
            document.getElementById('applicationForm').style.display = 'block';
            document.getElementById('confirmationPage').style.display = 'none';
        }

        function backToLanding() {
            document.getElementById('landingPage').style.display = 'block';
            document.getElementById('applicationForm').style.display = 'none';
            document.getElementById('confirmationPage').style.display = 'none';
            document.getElementById('candidateForm').reset();
            document.getElementById('fileName').textContent = '';
        }

        function displayFileName() {
            const input = document.getElementById('cvFile');
            const fileNameDiv = document.getElementById('fileName');
            if (input.files.length > 0) {
                fileNameDiv.textContent = '✓ ' + input.files[0].name;
                fileNameDiv.style.color = '#28a745';
            }
        }

        function showJD(position) {
            const modal = document.getElementById('jdModal');
            const jd = jobDescriptions[position];
            document.getElementById('jdTitle').textContent = jd.title;
            document.getElementById('jdContent').innerHTML = jd.content;
            modal.style.display = 'block';
        }

        function closeJD() {
            document.getElementById('jdModal').style.display = 'none';
        }

        window.onclick = function(event) {
            const modal = document.getElementById('jdModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }

        document.getElementById('candidateForm').addEventListener('submit', function(e) {
            e.preventDefault();

            const positionValue = document.getElementById('position').value;
            const positionText = document.getElementById('position').options[document.getElementById('position').selectedIndex].text;

            applicationData = {
                fullName: document.getElementById('fullName').value,
                email: document.getElementById('email').value,
                phone: document.getElementById('phone').value,
                address: document.getElementById('address').value,
                position: positionText,
                cvFile: document.getElementById('cvFile').files[0].name
            };

            document.getElementById('reviewName').textContent = applicationData.fullName;
            document.getElementById('reviewEmail').textContent = applicationData.email;
            document.getElementById('reviewPhone').textContent = applicationData.phone;
            document.getElementById('reviewAddress').textContent = applicationData.address;
            document.getElementById('reviewPosition').textContent = applicationData.position;
            document.getElementById('reviewCV').textContent = applicationData.cvFile;

            document.getElementById('landingPage').style.display = 'none';
            document.getElementById('applicationForm').style.display = 'none';
            document.getElementById('confirmationPage').style.display = 'block';
        });

        // Render created jobs from localStorage under the default list
        (function renderCreatedJobs() {
            try {
                const container = document.getElementById('jobListContainer');
                if (!container) return;
                const stored = JSON.parse(localStorage.getItem('createdJobs') || '[]');
                if (!Array.isArray(stored) || stored.length === 0) return;
                stored.forEach(job => {
                    const div = document.createElement('div');
                    div.className = 'job-item';
                    div.innerHTML = `
                        <h3>💼 ${job.title}</h3>
                        <p>📍 ${job.location || ''} | 💰 Lương: ${job.salary || 'Thỏa thuận'} | ⏰ ${job.status === 'active' ? 'Active' : 'Status: ' + (job.status || 'N/A')}</p>
                        <button class="view-jd-btn">Xem mô tả công việc</button>
                    `;
                    const btn = div.querySelector('.view-jd-btn');
                    btn.addEventListener('click', function() {
                        // Show JD modal with dynamic content
                        document.getElementById('jdTitle').textContent = job.title;
                        document.getElementById('jdContent').innerHTML = `
                            <h3>Mô tả công việc:</h3>
                            <p>${(job.description || '').replace(/\n/g, '<br>')}</p>
                            <h3>Thông tin:</h3>
                            <ul>
                                <li>Phòng ban: ${job.department || 'N/A'}</li>
                                <li>Địa điểm: ${job.location || 'N/A'}</li>
                                <li>Mức lương: ${job.salary || 'Thỏa thuận'}</li>
                                <li>Trạng thái: ${job.status || 'N/A'}</li>
                            </ul>
                        `;
                        document.getElementById('jdModal').style.display = 'block';
                    });
                    container.appendChild(div);
                });
            } catch (err) {
                console.error('Failed to render created jobs:', err);
            }
        })();
