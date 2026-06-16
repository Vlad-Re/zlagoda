import Modal from './Modal';

export default function ConfirmDialog({ message, onConfirm, onCancel, loading }) {
  return (
    <Modal
      title="Підтвердження"
      onClose={onCancel}
      onSubmit={onConfirm}
      submitLabel="Видалити"
      loading={loading}
    >
      <p>{message}</p>
    </Modal>
  );
}
