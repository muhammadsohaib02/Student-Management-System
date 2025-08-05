
$(document).ready(function() {
    console.log('student-api.js loaded successfully');
    function showModal(title, message, isSuccess) {
        if (!$('#responseModal').length) {
            console.error('Response modal not found in DOM');
            alert('Modal not found. Please ensure page structure is correct.');
            return;
        }
        $('#responseModalLabel').text(title);
        $('#responseModal .modal-body').text(message);
        $('#responseModal').modal('show');
        if (isSuccess) {
            setTimeout(() => window.location.reload(), 2000);
        }
    }
    $('#assign-subject-form').on('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        console.log('Submitting assign-subject form with data:', Array.from(formData.entries()));
        $.ajax({
            url: window.location.pathname,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log('Assign Subject Response:', response);
                showModal('Success', response.message || 'Subjects assigned successfully', true);
            },
            error: function(xhr, status, error) {
                console.error('Assign Subject Error:', xhr.responseText, status, error);
                let errorMessage = 'An error occurred while assigning the subject.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                showModal('Error', errorMessage, false);
            }
        });
    });
    $(document).on('click', '.unassign-subject', function() {
        const teacherId = $(this).data('teacher-id');
        const subjectId = $(this).data('subject-id');
        console.log('Unassign subject button clicked, teacher ID:', teacherId, 'subject ID:', subjectId);
        if (!teacherId || !subjectId) {
            console.error('Unassign button missing data attributes');
            showModal('Error', 'Invalid teacher or subject ID.', false);
            return;
        }
        if (confirm('Are you sure you want to unassign this subject?')) {
            $.ajax({
                url: `/unassign-subject/${teacherId}/${subjectId}`,
                type: 'POST',
                success: function(response) {
                    console.log('Unassign Subject Response:', response);
                    showModal('Success', response.message || 'Subject unassigned successfully', true);
                },
                error: function(xhr, status, error) {
                    console.error('Unassign Subject Error:', xhr.responseText, status, error);
                    let errorMessage = 'An error occurred while unassigning the subject.';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    showModal('Error', errorMessage, false);
                }
            });
        }
    });
    $('#add-teacher-form').on('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        $.ajax({
            url: '/add-teacher',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log('Add Teacher Response:', response);
                if (response.success) {
                    showModal('Success', response.message || 'Teacher added successfully', true);
                } else {
                    showModal('Error', response.message || 'Error adding teacher', false);
                }
            },
            error: function(xhr, status, error) {
                console.error('Add Teacher Error:', xhr.responseText, status, error);
                showModal('Error', 'An error occurred while adding the teacher.', false);
            }
        });
    });
    $(document).on('click', '.delete-teacher', function() {
        const teacherId = $(this).data('id');
        console.log('Delete teacher button clicked, teacher ID:', teacherId);
        if (!teacherId) {
            console.error('Delete button missing data-id attribute');
            showModal('Error', 'Invalid teacher ID. Please check button configuration.', false);
            return;
        }
        if (confirm('Are you sure you want to delete this teacher?')) {
            $.ajax({
                url: `/delete-teacher/${teacherId}`,
                type: 'POST',
                success: function(response) {
                    console.log('Delete Teacher Response:', response);
                    if (response.success) {
                        showModal('Success', response.message || 'Teacher deleted successfully', true);
                    } else {
                        showModal('Error', response.message || 'Error deleting teacher', false);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Delete Teacher Error:', xhr.responseText, status, error);
                    showModal('Error', 'An error occurred while deleting the teacher.', false);
                }
            });
        }
    });
    $('#edit-teacher-form').on('submit', function(e) {
        e.preventDefault();
        const teacherId = $('#edit_teacher_id').val();
        console.log('Edit teacher form submitted, teacher ID:', teacherId);
        if (!teacherId) {
            console.error('Edit form missing teacher ID');
            showModal('Error', 'Invalid teacher ID. Please try again.', false);
            return;
        }
        const formData = new FormData(this);
        $.ajax({
            url: `/edit-teacher/${teacherId}`,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log('Edit Teacher Response:', response);
                if (response.success) {
                    showModal('Success', response.message || 'Teacher updated successfully', true);
                    setTimeout(() => window.location.href = '/add-teacher', 2000);
                } else {
                    showModal('Error', response.message || 'Error updating teacher', false);
                }
            },
            error: function(xhr, status, error) {
                console.error('Edit Teacher Error:', xhr.responseText, status, error);
                showModal('Error', 'An error occurred while updating the teacher.', false);
            }
        });
    });
});
