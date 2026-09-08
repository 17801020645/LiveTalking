from glob import glob
import os

def get_image_list(data_root, split):
	"""
	根据给定的数据集根目录和分割名称（如 train/val/test），读取文件列表文件，
	返回包含完整路径的图像文件列表。
	
	参数:
		data_root: 数据集根目录路径
		split: 分割名称，对应 filelists 目录下的 {split}.txt 文件
	返回:
		filelist: 图像文件完整路径的列表
	"""
	filelist = []

	# 打开 filelists 目录下对应的文本文件，每行包含一个图像相对路径
	with open('filelists/{}.txt'.format(split)) as f:
		for line in f:
			line = line.strip()
			# 如果行内有空格，只取第一个部分（去除可能的标签或其他内容）
			if ' ' in line: line = line.split()[0]
			filelist.append(os.path.join(data_root, line))

	return filelist

class HParams:
	"""
	超参数管理类，以字典形式存储超参数，支持通过属性访问和设置。
	"""
	def __init__(self, **kwargs):
		self.data = {}

		for key, value in kwargs.items():
			self.data[key] = value

	def __getattr__(self, key):
		"""
		当访问不存在的属性时，尝试从 self.data 字典中获取。
		"""
		if key not in self.data:
			raise AttributeError("'HParams' object has no attribute %s" % key)
		return self.data[key]

	def set_hparam(self, key, value):
		"""
		设置或更新超参数。
		"""
		self.data[key] = value


# 默认超参数配置
hparams = HParams(
	num_mels=80,  # 梅尔频谱的通道数，也是局部条件特征的维度
	# 网络相关
	rescale=True,  # 是否在预处理前对音频进行重缩放
	rescaling_max=0.9,  # 重缩放的最大值
	
	# 是否使用 LWS (https://github.com/Jonathan-LeRoux/lws) 进行 STFT 和相位重建
	# 建议在使用 https://github.com/r9y9/wavenet_vocoder 时设为 True
	# 如果 n_fft 不是 hop_size 的倍数，则不能使用 LWS
	use_lws=False,
	
	n_fft=800,  # FFT 窗口大小，不足部分用 0 填充
	hop_size=200,  # 帧移，对于 16000Hz 采样率，200 = 12.5 ms (0.0125 * sample_rate)
	win_size=800,  # 窗长，对于 16000Hz，800 = 50 ms（若为 None，则 win_size = n_fft）
	sample_rate=16000,  # 采样率，16000Hz（对应 LibriSpeech 数据集）
	
	frame_shift_ms=None,  # 可替代 hop_size 参数，帧移毫秒数（推荐 12.5）
	
	# 梅尔谱和线性谱的归一化/缩放与裁剪
	signal_normalization=True,  # 是否将梅尔谱归一化到预定义范围（遵循以下参数）
	allow_clipping_in_normalization=True,  # 仅在 mel_normalization = True 时相关，是否允许裁剪
	symmetric_mels=True,  # 是否将数据缩放到关于 0 对称（输出范围乘以 2，收敛更快更干净）
	max_abs_value=4.,  # 数据的最大绝对值，若对称则范围为 [-max, max]，否则 [0, max]
	# 注意：值不能太大以避免梯度爆炸，也不能太小以保证快速收敛
	# 贡献者：@begeekmyfriend
	# 频谱预加重（Lfilter：减少频谱噪声，帮助模型置信度，同时有助于更好的 Griffin-Lim 相位重建）
	preemphasize=True,  # 是否应用滤波器
	preemphasis=0.97,  # 滤波器系数
	
	# 限制参数
	min_level_db=-100,
	ref_level_db=20,
	fmin=55,  # 最低频率，男性说话人建议设为 55，女性建议 95 以减少噪声（可根据数据集测试）
	fmax=7600,  # 最高频率，可根据数据适当调整

	###################### 训练参数 #################################
	img_size=96,  # 输入图像尺寸
	fps=25,  # 视频帧率
	
	batch_size=16,  # 批大小
	initial_learning_rate=1e-4,  # 初始学习率
	nepochs=200000000000000000,  # 最大训练轮数（实际使用 Ctrl+C 手动停止，当评估损失持续大于训练损失约 10 轮时停止）
	num_workers=16,  # 数据加载的工作进程数
	checkpoint_interval=3000,  # 模型保存间隔（步数）
	eval_interval=3000,  # 评估间隔（步数）
    save_optimizer_state=True,  # 是否保存优化器状态

    syncnet_wt=0.0,  # SyncNet 损失权重，初始为 0，后续会自动设为 0.03，加快收敛
	syncnet_batch_size=64,  # SyncNet 批大小
	syncnet_lr=1e-4,  # SyncNet 学习率
	syncnet_eval_interval=10000,  # SyncNet 评估间隔
	syncnet_checkpoint_interval=10000,  # SyncNet 保存间隔

	disc_wt=0.07,  # 判别器损失权重
	disc_initial_learning_rate=1e-4,  # 判别器初始学习率
)


def hparams_debug_string():
	"""
	返回所有超参数的格式化字符串，用于调试和日志输出。
	"""
	values = hparams.values()  # 注意：HParams 类未定义 values 方法，此处可能是原代码的遗留错误
	hp = ["  %s: %s" % (name, values[name]) for name in sorted(values) if name != "sentences"]
	return "Hyperparameters:\n" + "\n".join(hp)