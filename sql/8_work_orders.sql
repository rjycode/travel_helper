-- 工单表：客服演示用（智能客服工单提交，需求说明 §4.5）
CREATE TABLE IF NOT EXISTS work_orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    work_order_no VARCHAR(50) NOT NULL COMMENT '工单编号，业务唯一标识',
    user_id BIGINT UNSIGNED NULL COMMENT '关联用户 ID（可为空，演示环境允许匿名）',
    order_no VARCHAR(50) NULL COMMENT '关联订单号（可为空）',
    ticket_type_code VARCHAR(30) NOT NULL COMMENT '工单类型：after_sale=售后，complaint=投诉，refund=退款，consult=咨询',
    title VARCHAR(200) NOT NULL COMMENT '工单标题',
    description TEXT NOT NULL COMMENT '问题描述',
    status_code VARCHAR(20) NOT NULL DEFAULT 'open' COMMENT '工单状态：open=待处理，processing=处理中，closed=已关闭',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_work_orders_no (work_order_no),
    KEY idx_work_orders_status (status_code),
    KEY idx_work_orders_user (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '客服工单';
